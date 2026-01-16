"""
Real-time vibration monitoring server with WebSocket streaming.
Integrates serial handler, parameter calculator, and WebSocket broadcasting.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Set, Dict, Optional
import numpy as np
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager

from serial_handler import SerialHandler
from parameter_calculator import ParameterCalculator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealtimeMonitorServer:
    """Real-time vibration monitoring server with WebSocket support."""
    
    def __init__(self, app: FastAPI):
        """Initialize monitoring server."""
        self.app = app
        self.serial_handler = None
        self.param_calculator = ParameterCalculator(sampling_rate=50.0)
        
        # WebSocket connections
        self.active_connections: Set[WebSocket] = set()
        
        # State
        self.is_running = False
        self.current_recording = None
        self.recording_session_id = None
        self.update_queue = asyncio.Queue()
        self.update_interval = 0.1  # 100ms between updates (10Hz UI updates)
        
        # Recording data
        self.recordings_dir = Path(__file__).parent / "recordings"
        self.recordings_dir.mkdir(exist_ok=True)
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.on_event("startup")
        async def startup_event():
            await self.startup()
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            await self.shutdown()
        
        @self.app.websocket("/ws/monitor")
        async def websocket_endpoint(websocket: WebSocket):
            await self.handle_websocket(websocket)
        
        @self.app.get("/api/status")
        async def get_status():
            return self.get_server_status()
        
        @self.app.post("/api/start-recording")
        async def start_recording():
            return await self.start_recording()
        
        @self.app.post("/api/stop-recording")
        async def stop_recording():
            return await self.stop_recording()
        
        @self.app.get("/api/recordings")
        async def list_recordings():
            return self.list_recordings()
        
        @self.app.get("/api/recordings/{session_id}")
        async def get_recording(session_id: str):
            return self.get_recording(session_id)
    
    async def startup(self):
        """Initialize server on startup."""
        logger.info("Starting real-time monitoring server...")
        
        # Initialize serial handler
        self.serial_handler = SerialHandler()
        
        # Set callbacks
        self.serial_handler.set_callbacks(
            on_data_received=self._on_serial_data,
            on_recording_start=self._on_recording_start,
            on_recording_end=self._on_recording_end,
            on_error=self._on_serial_error
        )
        
        # Check connection
        status = self.serial_handler.get_status()
        logger.info(f"Serial status: {status}")
        
        self.is_running = True
        
        # Start parameter broadcasting task
        asyncio.create_task(self.broadcast_parameters())
        
        logger.info("Real-time monitoring server started")
    
    async def shutdown(self):
        """Cleanup on shutdown."""
        logger.info("Shutting down real-time monitoring server...")
        self.is_running = False
        
        if self.serial_handler:
            self.serial_handler.disconnect()
    
    async def handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        
        logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")
        
        try:
            # Send initial status
            await websocket.send_json({
                'type': 'connection',
                'status': 'connected',
                'server_status': self.get_server_status()
            })
            
            # Keep connection alive and listen for messages
            while True:
                try:
                    # Receive with timeout
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                    
                    # Handle incoming message
                    msg = json.loads(data)
                    await self._handle_client_message(websocket, msg)
                
                except asyncio.TimeoutError:
                    # Send heartbeat
                    await websocket.send_json({
                        'type': 'heartbeat',
                        'timestamp': datetime.now().isoformat()
                    })
        
        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
            self.active_connections.discard(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            self.active_connections.discard(websocket)
    
    async def _handle_client_message(self, websocket: WebSocket, msg: Dict):
        """Handle incoming WebSocket message."""
        msg_type = msg.get('type')
        
        if msg_type == 'ping':
            await websocket.send_json({'type': 'pong'})
        elif msg_type == 'request_status':
            await websocket.send_json({
                'type': 'status_update',
                'data': self.get_server_status()
            })
        else:
            logger.debug(f"Unknown message type: {msg_type}")
    
    def _on_serial_data(self, data_tuple):
        """Callback when new serial data received."""
        # Queue data for async processing
        try:
            asyncio.create_task(self._process_serial_data(data_tuple))
        except RuntimeError:
            # Event loop not running
            pass
    
    async def _process_serial_data(self, data_tuple):
        """Process serial data and broadcast to clients."""
        # Data format: (s1_x, s1_y, s1_z, s2_x, s2_y, s2_z)
        try:
            data_point = {
                'timestamp': datetime.now().isoformat(),
                'sensor_1': {
                    'x': float(data_tuple[0]),
                    'y': float(data_tuple[1]),
                    'z': float(data_tuple[2]),
                },
                'sensor_2': {
                    'x': float(data_tuple[3]),
                    'y': float(data_tuple[4]),
                    'z': float(data_tuple[5]),
                }
            }
            
            await self.update_queue.put(data_point)
        except Exception as e:
            logger.error(f"Error processing serial data: {e}")
    
    async def broadcast_parameters(self):
        """Periodically calculate and broadcast parameters."""
        while self.is_running:
            try:
                # Collect recent data
                sensor1_data, sensor2_data = self.serial_handler.get_latest_data(n_samples=1500)
                
                if len(sensor1_data) > 100:  # Need enough samples for calculation
                    # Calculate parameters
                    params = self.param_calculator.calculate_all_parameters(
                        sensor1_data, 
                        sensor2_data
                    )
                    
                    # Broadcast to all connected clients
                    await self._broadcast({
                        'type': 'parameters_update',
                        'timestamp': datetime.now().isoformat(),
                        'data': params
                    })
                
                await asyncio.sleep(self.update_interval)
            
            except Exception as e:
                logger.error(f"Error broadcasting parameters: {e}")
                await asyncio.sleep(1)
    
    async def _broadcast(self, message: Dict):
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return
        
        # Convert numpy types to Python types for JSON serialization
        message_json = self._serialize_for_json(message)
        message_str = json.dumps(message_json)
        
        # Broadcast to all clients
        disconnected = set()
        for websocket in self.active_connections:
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.debug(f"Error sending to client: {e}")
                disconnected.add(websocket)
        
        # Remove disconnected clients
        self.active_connections -= disconnected
    
    def _serialize_for_json(self, obj):
        """Convert numpy types to JSON-serializable types."""
        if isinstance(obj, dict):
            return {k: self._serialize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._serialize_for_json(item) for item in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj
    
    def _on_recording_start(self):
        """Callback when recording starts."""
        logger.info("Recording started on Arduino")
        
        try:
            asyncio.create_task(self._broadcast({
                'type': 'recording_started',
                'timestamp': datetime.now().isoformat()
            }))
        except RuntimeError:
            pass
    
    def _on_recording_end(self):
        """Callback when recording ends."""
        logger.info("Recording ended on Arduino")
        
        try:
            asyncio.create_task(self._broadcast({
                'type': 'recording_ended',
                'timestamp': datetime.now().isoformat()
            }))
        except RuntimeError:
            pass
    
    def _on_serial_error(self, error_msg: str):
        """Callback when serial error occurs."""
        logger.error(f"Serial error: {error_msg}")
        
        try:
            asyncio.create_task(self._broadcast({
                'type': 'error',
                'message': error_msg,
                'timestamp': datetime.now().isoformat()
            }))
        except RuntimeError:
            pass
    
    async def start_recording(self) -> Dict:
        """Start a recording session."""
        if not self.serial_handler:
            return {'error': 'Serial handler not initialized'}
        
        # Start recording on Arduino
        success = self.serial_handler.start_recording()
        
        if success:
            self.recording_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            return {
                'status': 'recording_started',
                'session_id': self.recording_session_id
            }
        else:
            return {
                'error': 'Failed to start recording',
                'details': self.serial_handler.last_error
            }
    
    async def stop_recording(self) -> Dict:
        """Stop current recording session."""
        if not self.serial_handler:
            return {'error': 'Serial handler not initialized'}
        
        try:
            # Stop recording on Arduino
            sensor1_data, sensor2_data = self.serial_handler.stop_recording()
            
            if len(sensor1_data) == 0:
                return {'error': 'No data recorded'}
            
            # Save recording
            session_id = self.recording_session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
            recording_path = self.recordings_dir / f"{session_id}.npy"
            
            np.save(
                recording_path,
                {
                    'sensor_1': sensor1_data,
                    'sensor_2': sensor2_data,
                    'timestamp': datetime.now().isoformat(),
                    'samples': len(sensor1_data),
                    'sampling_rate': 50.0
                },
                allow_pickle=True
            )
            
            # Calculate parameters for recorded data
            params = self.param_calculator.calculate_all_parameters(sensor1_data, sensor2_data)
            
            # Save parameters
            params_path = self.recordings_dir / f"{session_id}_params.json"
            with open(params_path, 'w') as f:
                json.dump(self._serialize_for_json(params), f, indent=2)
            
            logger.info(f"Recording saved: {session_id}")
            
            return {
                'status': 'recording_stopped',
                'session_id': session_id,
                'samples': len(sensor1_data),
                'parameters': params
            }
        
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return {'error': str(e)}
    
    def get_server_status(self) -> Dict:
        """Get current server status."""
        if not self.serial_handler:
            return {'error': 'Serial handler not initialized'}
        
        serial_status = self.serial_handler.get_status()
        
        return {
            'server_running': self.is_running,
            'active_connections': len(self.active_connections),
            'serial': serial_status,
            'recording_session': self.recording_session_id,
            'timestamp': datetime.now().isoformat()
        }
    
    def list_recordings(self) -> Dict:
        """List all saved recordings."""
        recordings = []
        
        for npy_file in self.recordings_dir.glob("*.npy"):
            session_id = npy_file.stem
            params_file = self.recordings_dir / f"{session_id}_params.json"
            
            try:
                data = np.load(npy_file, allow_pickle=True).item()
                params = {}
                
                if params_file.exists():
                    with open(params_file, 'r') as f:
                        params = json.load(f)
                
                recordings.append({
                    'session_id': session_id,
                    'timestamp': data.get('timestamp'),
                    'samples': data.get('samples'),
                    'sampling_rate': data.get('sampling_rate'),
                    'has_parameters': bool(params)
                })
            except Exception as e:
                logger.error(f"Error reading recording {session_id}: {e}")
        
        return {
            'recordings': sorted(recordings, key=lambda x: x['timestamp'], reverse=True)
        }
    
    def get_recording(self, session_id: str) -> Dict:
        """Get specific recording data."""
        npy_file = self.recordings_dir / f"{session_id}.npy"
        params_file = self.recordings_dir / f"{session_id}_params.json"
        
        if not npy_file.exists():
            return {'error': f'Recording {session_id} not found'}
        
        try:
            data = np.load(npy_file, allow_pickle=True).item()
            params = {}
            
            if params_file.exists():
                with open(params_file, 'r') as f:
                    params = json.load(f)
            
            return {
                'session_id': session_id,
                'metadata': {
                    'timestamp': data.get('timestamp'),
                    'samples': data.get('samples'),
                    'sampling_rate': data.get('sampling_rate'),
                },
                'parameters': params
            }
        
        except Exception as e:
            return {'error': str(e)}


# Create FastAPI app with startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    monitor = RealtimeMonitorServer(app)
    app.state.monitor = monitor
    
    # Start parameter broadcasting
    broadcast_task = asyncio.create_task(monitor.broadcast_parameters())
    
    yield
    
    # Shutdown
    broadcast_task.cancel()
    await monitor.shutdown()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Real-time Vibration Monitor",
        description="Dual-sensor ADXL345 vibration monitoring system",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app


if __name__ == "__main__":
    import uvicorn
    
    app = create_app()
    
    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
