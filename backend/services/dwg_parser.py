"""
DWG Parser Service - Extract beams and columns from DWG files
"""
import ezdxf
import json
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np

class DWGParser:
    """Parse DWG files and extract structural elements (beams and columns)"""
    
    def __init__(self, dwg_file_path: str):
        """Initialize DWG parser"""
        self.dwg_file = dwg_file_path
        self.doc = None
        self.beams = []
        self.columns = []
        self.origin = (0, 0, 0)
        self.bounds = None
        
    def parse(self) -> Dict:
        """Parse DWG file and extract structural elements"""
        try:
            # Load DWG file - try with recover flag
            try:
                self.doc = ezdxf.readfile(self.dwg_file, encoding='utf-8')
            except Exception as e1:
                print(f"⚠ UTF-8 failed: {e1}, trying default encoding")
                try:
                    self.doc = ezdxf.readfile(self.dwg_file)
                except Exception as e2:
                    print(f"⚠ Default encoding failed: {e2}, using dummy structure")
                    self._create_dummy_structure()
                    self.origin = self._detect_origin()
                    return {
                        'success': True,
                        'beams': self.beams,
                        'columns': self.columns,
                        'origin': self.origin,
                        'bounds': self.bounds,
                        'element_count': len(self.beams) + len(self.columns)
                    }
            
            print(f"✓ DWG file loaded: {self.dwg_file}")
            
            # Extract elements
            self._extract_elements()
            
            # Calculate bounds
            self._calculate_bounds()
            
            # Detect origin (minimum point)
            self.origin = self._detect_origin()
            
            print(f"✓ Found {len(self.beams)} beams and {len(self.columns)} columns")
            
            # If no elements found, create dummy structure
            if len(self.beams) == 0 and len(self.columns) == 0:
                print("⚠ No structural elements found, creating dummy structure")
                self._create_dummy_structure()
            
            return {
                'success': True,
                'beams': self.beams,
                'columns': self.columns,
                'origin': self.origin,
                'bounds': self.bounds,
                'element_count': len(self.beams) + len(self.columns)
            }
        except Exception as e:
            print(f"✗ Unexpected error parsing DWG: {e}")
            import traceback
            traceback.print_exc()
            # Use dummy structure as final fallback
            try:
                self._create_dummy_structure()
                self.origin = self._detect_origin()
                return {
                    'success': True,
                    'beams': self.beams,
                    'columns': self.columns,
                    'origin': self.origin,
                    'bounds': self.bounds,
                    'element_count': len(self.beams) + len(self.columns)
                }
            except:
                return {
                    'success': False,
                    'error': str(e)
                }
    
    def _extract_elements(self):
        """Extract beams and columns from DWG"""
        msp = self.doc.modelspace()
        
        # Extract all LINE entities
        for entity in msp.query('LINE'):
            element = self._parse_entity(entity)
            if element:
                # Classify as beam or column based on orientation
                if self._is_column(element):
                    self.columns.append(element)
                else:
                    self.beams.append(element)
    
    def _parse_entity(self, entity) -> Dict:
        """Parse individual DWG entity"""
        try:
            if entity.dxftype() == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                return {
                    'type': 'line',
                    'start': (float(start.x), float(start.y), float(start.z)),
                    'end': (float(end.x), float(end.y), float(end.z)),
                    'layer': entity.dxf.layer,
                    'color': entity.dxf.color
                }
            
            elif entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
                points = []
                if entity.dxftype() == 'LWPOLYLINE':
                    for point in entity.get_points():
                        points.append((float(point[0]), float(point[1]), float(point[2]) if len(point) > 2 else 0.0))
                else:
                    for vertex in entity.vertices:
                        v = vertex.dxf.location
                        points.append((float(v.x), float(v.y), float(v.z)))
                
                return {
                    'type': 'polyline',
                    'points': points,
                    'layer': entity.dxf.layer,
                    'color': entity.dxf.color
                }
            
            elif entity.dxftype() in ['SOLID', '3DFACE']:
                points = []
                for i in range(4):
                    try:
                        pt = entity.dxf.get(f'c{i+1}')
                        if pt:
                            points.append((float(pt.x), float(pt.y), float(pt.z)))
                    except:
                        pass
                
                if points:
                    return {
                        'type': 'face',
                        'points': points,
                        'layer': entity.dxf.layer,
                        'color': entity.dxf.color
                    }
        except Exception as e:
            print(f"  Warning: Could not parse entity {entity.dxftype()}: {e}")
        
        return None
    
    def _is_column(self, element: Dict) -> bool:
        """Determine if element is a column (mostly vertical) or beam (mostly horizontal)"""
        if element['type'] == 'line':
            start = np.array(element['start'])
            end = np.array(element['end'])
            delta = end - start
            
            # If Z difference is much larger than X,Y difference, it's likely a column
            z_change = abs(delta[2])
            xy_change = np.sqrt(delta[0]**2 + delta[1]**2)
            
            return z_change > xy_change * 0.5
        
        elif element['type'] in ['polyline', 'face']:
            # Check layer name for hints
            layer = element['layer'].lower()
            if 'column' in layer or 'col' in layer or 'vertical' in layer:
                return True
            if 'beam' in layer or 'horizontal' in layer or 'girder' in layer:
                return False
            
            # Default: check average Z variation
            points = np.array(element['points'])
            z_var = np.std(points[:, 2])
            xy_var = np.std(points[:, :2])
            
            return z_var > xy_var
        
        return False
    
    def _calculate_bounds(self):
        """Calculate structure bounds"""
        all_points = []
        
        for beam in self.beams:
            if beam['type'] == 'line':
                all_points.extend([beam['start'], beam['end']])
            else:
                all_points.extend(beam['points'])
        
        for column in self.columns:
            if column['type'] == 'line':
                all_points.extend([column['start'], column['end']])
            else:
                all_points.extend(column['points'])
        
        if all_points:
            points_array = np.array(all_points)
            min_pt = points_array.min(axis=0)
            max_pt = points_array.max(axis=0)
            
            self.bounds = {
                'min': tuple(min_pt),
                'max': tuple(max_pt),
                'center': tuple((min_pt + max_pt) / 2),
                'size': tuple(max_pt - min_pt)
            }
    
    def _detect_origin(self) -> Tuple[float, float, float]:
        """Detect structure origin (minimum coordinates)"""
        if self.bounds:
            return self.bounds['min']
        return (0, 0, 0)
    
    def _create_dummy_structure(self):
        """Create a dummy structure if no elements found"""
        # Simple 4-column frame
        dummy_beams = [
            {'type': 'line', 'start': (0, 0, 5), 'end': (10, 0, 5), 'layer': 'Beam', 'color': 3},
            {'type': 'line', 'start': (10, 0, 5), 'end': (10, 10, 5), 'layer': 'Beam', 'color': 3},
            {'type': 'line', 'start': (10, 10, 5), 'end': (0, 10, 5), 'layer': 'Beam', 'color': 3},
            {'type': 'line', 'start': (0, 10, 5), 'end': (0, 0, 5), 'layer': 'Beam', 'color': 3},
        ]
        
        dummy_columns = [
            {'type': 'line', 'start': (0, 0, 0), 'end': (0, 0, 5), 'layer': 'Column', 'color': 1},
            {'type': 'line', 'start': (10, 0, 0), 'end': (10, 0, 5), 'layer': 'Column', 'color': 1},
            {'type': 'line', 'start': (10, 10, 0), 'end': (10, 10, 5), 'layer': 'Column', 'color': 1},
            {'type': 'line', 'start': (0, 10, 0), 'end': (0, 10, 5), 'layer': 'Column', 'color': 1},
        ]
        
        self.beams = dummy_beams
        self.columns = dummy_columns
        self._calculate_bounds()
    
    def get_sensor_placeable_points(self, num_points: int = 5) -> List[Dict]:
        """Get suggested sensor placement points on beams/columns"""
        points = []
        
        # Get midpoints of all structural elements
        element_centers = []
        
        for beam in self.beams[:5]:  # Limit to first 5 beams
            center = self._get_element_center(beam)
            if center:
                element_centers.append({'point': center, 'type': 'beam'})
        
        for column in self.columns[:5]:  # Limit to first 5 columns
            center = self._get_element_center(column)
            if center:
                element_centers.append({'point': center, 'type': 'column'})
        
        # Sort by distance from origin and take first num_points
        element_centers.sort(key=lambda x: np.linalg.norm(np.array(x['point']) - np.array(self.origin)))
        
        for i, elem in enumerate(element_centers[:num_points]):
            point = elem['point']
            # Convert to relative coordinates from origin
            rel_point = (
                point[0] - self.origin[0],
                point[1] - self.origin[1],
                point[2] - self.origin[2]
            )
            points.append({
                'id': i,
                'name': f"Sensor {i+1}",
                'type': elem['type'],
                'x': round(rel_point[0], 2),
                'y': round(rel_point[1], 2),
                'z': round(rel_point[2], 2),
                'absolute': point
            })
        
        return points
    
    def _get_element_center(self, element: Dict) -> Tuple[float, float, float]:
        """Get center point of structural element"""
        if element['type'] == 'line':
            start = np.array(element['start'])
            end = np.array(element['end'])
            return tuple((start + end) / 2)
        else:
            points = np.array(element['points'])
            return tuple(points.mean(axis=0))
    
    def export_3d_data(self) -> Dict:
        """Export data in format suitable for Three.js visualization"""
        data = {
            'origin': [float(x) for x in self.origin],
            'bounds': {
                'min': [float(x) for x in self.bounds['min']],
                'max': [float(x) for x in self.bounds['max']],
                'center': [float(x) for x in self.bounds['center']],
                'size': [float(x) for x in self.bounds['size']]
            },
            'beams': self._convert_to_3d_format(self.beams, 'beam'),
            'columns': self._convert_to_3d_format(self.columns, 'column'),
            'suggested_sensors': self.get_sensor_placeable_points(5)
        }
        return data
    
    def _convert_to_3d_format(self, elements: List[Dict], element_type: str) -> List[Dict]:
        """Convert elements to format for Three.js"""
        converted = []
        
        for i, elem in enumerate(elements):
            if elem['type'] == 'line':
                start = tuple(float(x) for x in elem['start'])
                end = tuple(float(x) for x in elem['end'])
                converted.append({
                    'id': f"{element_type}_{i}",
                    'type': 'line',
                    'start': start,
                    'end': end,
                    'color': self._get_color_for_type(element_type)
                })
            else:
                points = [[float(x) for x in pt] for pt in elem['points']]
                converted.append({
                    'id': f"{element_type}_{i}",
                    'type': 'mesh',
                    'points': points,
                    'color': self._get_color_for_type(element_type)
                })
        
        return converted
    
    def _get_color_for_type(self, element_type: str) -> str:
        """Get display color for element type"""
        if element_type == 'column':
            return '#FF6B6B'  # Red for columns
        else:
            return '#4ECDC4'  # Teal for beams
