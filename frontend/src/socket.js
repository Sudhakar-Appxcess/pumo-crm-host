import { io } from 'socket.io-client'
import { socketio_port } from '../../../../sites/common_site_config.json'
import { getCachedListResource } from 'frappe-ui/src/resources/listResource'
import { getCachedResource } from 'frappe-ui/src/resources/resources'

export function initSocket() {
  let host = window.location.hostname
  let siteName = window.site_name
  let port = window.location.port ? `:${socketio_port}` : ''
  let protocol = port ? 'http' : 'https'
  let url = `${protocol}://${host}${port}/${siteName}`

  let socket = io(url, {
    withCredentials: true,
    reconnectionAttempts: 10, // Increased from 5
    reconnectionDelay: 1000, // Start with 1 second
    reconnectionDelayMax: 5000, // Max 5 seconds between attempts
    timeout: 20000, // 20 second timeout
    transports: ['websocket', 'polling'], // Try websocket first, fallback to polling
    upgrade: true, // Allow transport upgrades
    rememberUpgrade: false, // Don't remember transport upgrade
  })

  // Handle session ID errors by forcing reconnection
  socket.on('connect_error', (error) => {
    const errorMsg = error.message || ''
    if (errorMsg.includes('Session ID unknown') || errorMsg.includes('session')) {
      console.warn('Socket session expired, reconnecting...')
      // Disconnect and force a fresh connection
      socket.disconnect()
      setTimeout(() => {
        if (!socket.connected) {
          socket.connect()
        }
      }, 1000)
    } else {
      console.error('Socket connection error:', errorMsg)
    }
  })

  // Handle disconnection
  socket.on('disconnect', (reason) => {
    if (reason === 'io server disconnect') {
      // Server disconnected the socket, reconnect manually
      socket.connect()
    }
    console.log('Socket disconnected:', reason)
  })

  // Handle successful reconnection
  socket.on('reconnect', (attemptNumber) => {
    console.log(`Socket reconnected after ${attemptNumber} attempts`)
  })

  // Handle connection
  socket.on('connect', () => {
    console.log('Socket connected successfully')
  })

  socket.on('refetch_resource', (data) => {
    if (data.cache_key) {
      let resource =
        getCachedResource(data.cache_key) ||
        getCachedListResource(data.cache_key)
      if (resource) {
        resource.reload()
      }
    }
  })

  return socket
}