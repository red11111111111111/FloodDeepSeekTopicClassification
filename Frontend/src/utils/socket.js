// src/utils/socket.js
import { io } from "socket.io-client";

const socket = io("http://localhost:5004", {
  transports: ["websocket"],   // 强制 WebSocket
  reconnection: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 2000,
});

export default socket;
