import { io } from 'socket.io-client'
import { socketio_port } from '../../../../sites/common_site_config.json'
import { getCachedListResource } from 'frappe-ui/src/resources/listResource'
import { getCachedResource } from 'frappe-ui/src/resources/resources'

export function initSocket() {
  let host = window.location.hostname
  let siteName = window.site_name
  let port = window.location.port ? `:${socketio_port}` : ''
  let protocol = port ? 'http' : 'https'
  // Base URL - Socket.IO will append the path and namespace
  // For HTTPS, Socket.IO will automatically use WSS (secure WebSocket)
  let baseUrl = `${protocol}://${host}${port}`
  // Namespace is the site name
  let namespace = `/${siteName}`

  // Connect to /ws/ path which is proxied by Nginx to backend Socket.IO server
  // path option tells Socket.IO where the socket.io endpoint is served
  // This will connect to: wss://adzday.com/ws/socket.io/?EIO=4&transport=websocket&nsp=/pumo.localhost
  let socket = io(baseUrl + namespace, {
    path: '/ws/socket.io',
    withCredentials: true,
    reconnectionAttempts: 5,
    transports: ['websocket'],
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