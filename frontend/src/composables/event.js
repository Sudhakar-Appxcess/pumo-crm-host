import { usersStore } from '@/stores/users'
import { dayjs, createListResource, call } from 'frappe-ui'
import { sameArrayContents } from '@/utils'
import { computed, ref, watch } from 'vue'
import { allTimeSlots } from '@/components/Calendar/utils'

export const showEventModal = ref(false)
export const activeEvent = ref(null)

export function useEvent(doctype, docname) {
  const { getUser } = usersStore()

  // Use custom API to bypass Frappe's field validation restrictions on reference_doctype
  const eventsData = ref([])
  const eventsLoading = ref(false)
  const eventsError = ref(null)

  const loadEvents = async () => {
    // Handle both ref values and direct values
    const doctypeValue = typeof doctype === 'object' && 'value' in doctype ? doctype.value : doctype
    const docnameValue = typeof docname === 'object' && 'value' in docname ? docname.value : docname
    
    if (!doctypeValue || !docnameValue) {
      eventsData.value = []
      return
    }

    eventsLoading.value = true
    eventsError.value = null
    try {
      const events = await call('crm.api.event.get_events_by_reference', {
        doctype: doctypeValue,
        docname: docnameValue,
      })
      eventsData.value = events || []
    } catch (error) {
      console.error('Error loading events:', error)
      eventsError.value = error
      eventsData.value = []
    } finally {
      eventsLoading.value = false
    }
  }

  // Load events when doctype/docname change - handles both refs and direct values
  // Use computed to handle both reactive props and direct values
  const doctypeRef = computed(() => typeof doctype === 'object' && 'value' in doctype ? doctype.value : doctype)
  const docnameRef = computed(() => typeof docname === 'object' && 'value' in docname ? docname.value : docname)
  
  watch([doctypeRef, docnameRef], () => {
    loadEvents()
  }, { immediate: true })

  // Create a resource-like object to maintain compatibility with existing code
  const eventsResource = {
    data: computed(() => eventsData.value),
    loading: computed(() => eventsLoading.value),
    error: computed(() => eventsError.value),
    reload: loadEvents,
    list: {
      loading: computed(() => eventsLoading.value)
    },
    setValue: {
      data: ref(null)
    },
    update: () => {}, // No-op for compatibility
  }

  const eventParticipantsResource = createListResource({
    doctype: 'Event Participants',
    fields: [
      'name',
      'parent',
      'parenttype', 
      'parentfield',
      'email',
      'reference_docname'
    ],
    parent: 'Event',
    onError: (error) => {
      console.warn('Event Participants query failed:', error)
      // Don't throw error, just log it and continue without participants
    }
  })

  const events = computed(() => {
    const eventsList = eventsResource.data.value || []
    if (!eventsList.length) return []
    
    // Create a copy to avoid mutating the original
    const processedEvents = eventsList.map(event => ({ ...event }))
    
    // Process events without participants if the query fails
    processedEvents.forEach((event) => {
      if (typeof event.owner !== 'object') {
        event.owner = {
          label: getUser(event.owner).full_name,
          image: getUser(event.owner).user_image,
          name: event.owner,
        }
      }

      // Only process participants if the resource is available and not in error state
      if (eventParticipantsResource.data && !eventParticipantsResource.error) {
        const eventNames = processedEvents.map((e) => e.name)
        if (
          !eventParticipantsResource.data?.length ||
          eventsParticipantIsUpdated(eventNames)
        ) {
          eventParticipantsResource.update({
            filters: {
              parenttype: 'Event',
              parentfield: 'event_participants',
              parent: ['in', eventNames],
            },
          })
          !eventParticipantsResource.list.loading &&
            eventParticipantsResource.reload()
        }

        event.event_participants = [
          ...eventParticipantsResource.data.filter(
            (participant) => participant.parent === event.name,
          ),
        ]

        event.participants = [
          event.owner,
          ...eventParticipantsResource.data
            .filter((participant) => participant.parent === event.name)
            .map((participant) => ({
              label: getUser(participant.email).full_name || participant.email,
              image: getUser(participant.email).user_image || '',
              name: participant.email,
            })),
        ]
      } else {
        // Fallback: no participants if query fails
        event.event_participants = []
        event.participants = [event.owner]
      }
    })

    return processedEvents
  })

  function eventsParticipantIsUpdated(eventNames) {
    const parentFilter = eventParticipantsResource.filters?.parent?.[1]

    if (eventNames.length && !sameArrayContents(parentFilter, eventNames))
      return true

    let d = eventsResource.setValue.data
    if (!d) return false

    let newParticipants = d.event_participants.map((p) => p.name)
    let oldParticipants = eventParticipantsResource.data
      .filter((p) => p.parent === d.name)
      .map((p) => p.name)

    return !sameArrayContents(newParticipants, oldParticipants)
  }

  const startEndTime = (
    startTime,
    endTime,
    isFullDay = false,
    format = 'h:mm a',
  ) => {
    const start = dayjs(startTime)
    const end = dayjs(endTime)

    if (isFullDay) return __('All day')

    return `${start.format(format)} - ${end.format(format)}`
  }

  const startDate = (startTime, format = 'ddd, D MMM YYYY') => {
    const start = dayjs(startTime)
    return start.format(format)
  }

  return {
    eventsResource,
    eventParticipantsResource,
    events,
    startEndTime,
    startDate,
  }
}

export function normalizeParticipants(list = []) {
  const seen = new Set()
  const out = []
  for (const a of list || []) {
    if (!a?.email || seen.has(a.email)) continue
    seen.add(a.email)
    
    // Only include email - the API will handle reference creation
    const participant = { email: a.email }
    
    // Only add reference fields if they exist and are valid
    if (a.reference_doctype && a.reference_docname && a.reference_docname !== '') {
      participant.reference_doctype = a.reference_doctype
      participant.reference_docname = a.reference_docname
    }
    
    out.push(participant)
  }
  return out
}

export function formatDuration(mins) {
  if (mins < 60) return __('{0} mins', [mins])
  let hours = mins / 60
  if (hours % 1 !== 0 && hours % 1 !== 0.5) {
    hours = hours.toFixed(2)
  }
  if (Number.isInteger(hours)) {
    return hours === 1 ? __('1 hr') : __('{0} hrs', [hours])
  }
  return `${hours} hrs`
}

export function buildEndTimeOptions(fromTime) {
  const timeSlots = allTimeSlots()
  if (!fromTime) return timeSlots
  const startIndex = timeSlots.findIndex((o) => o.value > fromTime)
  if (startIndex === -1) return []
  const [fh, fm] = fromTime.split(':').map((n) => parseInt(n))
  const fromTotal = fh * 60 + fm
  return timeSlots.slice(startIndex).map((o) => {
    const [th, tm] = o.value.split(':').map((n) => parseInt(n))
    const toTotal = th * 60 + tm
    const duration = toTotal - fromTotal
    return { ...o, label: `${o.label} (${formatDuration(duration)})` }
  })
}

export function computeAutoToTime(fromTime) {
  if (!fromTime) return ''
  const [hour, minute] = fromTime.split(':').map((n) => parseInt(n))
  let nh = hour + 1
  let nm = minute
  if (nh >= 24) {
    nh = 23
    nm = 59
  }
  return `${String(nh).padStart(2, '0')}:${String(nm).padStart(2, '0')}`
}

export function validateTimeRange({ fromDate, fromTime, toTime, isFullDay }) {
  if (isFullDay) return { valid: true, error: null }
  if (!fromTime || !toTime) {
    return { valid: false, error: __('Start and end time are required') }
  }
  const start = dayjs(fromDate + ' ' + fromTime)
  const end = dayjs(fromDate + ' ' + toTime)
  if (!start.isValid() || !end.isValid()) {
    return { valid: false, error: __('Invalid start or end time') }
  }
  if (end.diff(start, 'minute') <= 0) {
    return { valid: false, error: __('End time should be after start time') }
  }
  return { valid: true, error: null }
}

export function parseEventDoc(doc) {
  if (!doc) return {}
  const { getUser } = usersStore()
  return {
    id: doc.name,
    title: doc.subject,
    description: doc.description,
    status: doc.status,
    fromDate: dayjs(doc.starts_on).format('YYYY-MM-DD'),
    toDate: dayjs(doc.ends_on).format('YYYY-MM-DD'),
    fromTime: dayjs(doc.starts_on).format('HH:mm'),
    toTime: dayjs(doc.ends_on).format('HH:mm'),
    isFullDay: doc.all_day,
    eventType: doc.event_type,
    color: doc.color,
    referenceDoctype: doc.reference_doctype,
    referenceDocname: doc.reference_docname,
    event_participants: doc.event_participants || [],
    owner: doc.owner
      ? {
          label: getUser(doc.owner).full_name,
          image: getUser(doc.owner).user_image,
          value: doc.owner,
        }
      : null,
  }
}
