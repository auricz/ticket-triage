import { io, type Socket } from 'socket.io-client'
import type { Ticket } from '../types'

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL ?? 'http://localhost:4000'

type TicketHandler = (ticket: Ticket) => void

let socket: Socket | null = null
let onCreated: TicketHandler = () => {}
let onUpdated: TicketHandler = () => {}

export function registerTicketHandlers(handlers: { onCreated: TicketHandler; onUpdated: TicketHandler }) {
  onCreated = handlers.onCreated
  onUpdated = handlers.onUpdated
}

export function connectSocket(token: string) {
  socket?.disconnect()
  socket = io(SOCKET_URL, { auth: { token } })
  socket.on('ticket_created', (ticket: Ticket) => onCreated(ticket))
  socket.on('ticket_updated', (ticket: Ticket) => onUpdated(ticket))
}

export function disconnectSocket() {
  socket?.disconnect()
  socket = null
}
