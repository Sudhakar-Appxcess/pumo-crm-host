<template>
  <div
    class="flex flex-col gap-2 my-2 w-[470px] rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black p-3 ring-opacity-5 focus:outline-none"
  >
    <div class="text-base text-ink-gray-5">{{ __('Assign to') }}</div>
    <Link
      class="form-control"
      value=""
      doctype="User"
      @change="(option) => addValue(option) && ($refs.input.value = '')"
      :placeholder="__('John Doe')"
      :filters="{
        name: ['in', users.data.crmUsers?.map((user) => user.name)],
      }"
      :hideMe="true"
    >
      <template #target="{ togglePopover }">
        <div
          class="w-full min-h-12 flex flex-wrap items-center gap-1.5 p-1.5 pb-5 rounded-lg bg-surface-gray-2 cursor-text"
          @click.stop="togglePopover"
        >
          <Tooltip
            :text="assignee.name"
            v-for="assignee in assignees"
            :key="assignee.name"
            @click.stop
          >
            <div
              class="flex items-center text-sm p-0.5 text-ink-gray-6 border border-outline-gray-1 bg-surface-modal rounded-full cursor-pointer"
              @click.stop
            >
              <UserAvatar :user="assignee.name" size="sm" />
              <div class="ml-1">{{ getUser(assignee.name).full_name }}</div>
              <Button
                variant="ghost"
                class="rounded-full !size-4 m-1"
                @click.stop="removeValue(assignee.name)"
              >
                <template #icon>
                  <FeatherIcon name="x" class="h-3 w-3 text-ink-gray-6" />
                </template>
              </Button>
            </div>
          </Tooltip>
        </div>
      </template>
      <template #item-prefix="{ option }">
        <UserAvatar class="mr-2" :user="option.value" size="sm" />
      </template>
      <template #item-label="{ option }">
        <Tooltip :text="option.value">
          <div class="cursor-pointer text-ink-gray-9">
            {{ getUser(option.value).full_name }}
          </div>
        </Tooltip>
      </template>
    </Link>
    <div class="flex items-center justify-between gap-2">
      <div
        class="text-base text-ink-gray-5 cursor-pointer select-none"
        @click="assignToMe = !assignToMe"
      >
        {{ __('Assign to me') }}
      </div>
      <Switch v-model="assignToMe" @click.stop />
    </div>
    
    <!-- Reason field -->
    <div class="mt-3">
      <label class="block text-sm font-medium text-ink-gray-7 mb-1">
        {{ __('Reason for reassignment') }} <span class="text-red-500">*</span>
      </label>
      <TextEditor
        v-model="reassignmentReason"
        :placeholder="__('Please provide a reason for this reassignment...')"
        :min-height="80"
        :max-height="120"
        class="w-full"
        @change="(value) => reassignmentReason = value"
      />
      <div v-if="!reassignmentReason && showValidationError" class="text-red-500 text-xs mt-1">
        {{ __('Reason is required for reassignment') }}
      </div>
      
    </div>
    
    <!-- Save button -->
    <div class="mt-4 flex justify-end gap-2">
      <Button
        variant="ghost"
        :label="__('Cancel')"
        @click="$emit('close')"
      />
      <Button
        variant="solid"
        :label="__('Save')"
        @click="saveReassignment"
        :loading="isSaving"
        :disabled="!isReasonValid"
      />
    </div>
  </div>
</template>

<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import Link from '@/components/Controls/Link.vue'
import { usersStore } from '@/stores/users'
import { capture } from '@/telemetry'
import { Tooltip, Switch, createResource, TextEditor, Button, toast } from 'frappe-ui'
import { ref, watch, computed } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    default: '',
  },
  docname: {
    type: Object,
    default: null,
  },
  open: {
    type: Boolean,
    default: false,
  },
  onUpdate: {
    type: Function,
    default: null,
  },
})

const assignees = defineModel()
const oldAssignees = ref([])
const assignToMe = ref(false)
const reassignmentReason = ref('')
const showValidationError = ref(false)
const isSaving = ref(false)

const error = ref('')

const { users, getUser } = usersStore()

const emit = defineEmits(['reload', 'close'])

// Computed property to check if reason is valid
const isReasonValid = computed(() => {
  return reassignmentReason.value && reassignmentReason.value.trim().length > 0
})

const removeValue = (value) => {
  if (value === getUser('').name) {
    assignToMe.value = false
  }

  assignees.value = assignees.value.filter(
    (assignee) => assignee.name !== value,
  )
}

const addValue = (value) => {
  if (value === getUser('').name) {
    assignToMe.value = true
  }

  error.value = ''
  let obj = {
    name: value,
    image: getUser(value).user_image,
    label: getUser(value).full_name,
  }
  if (!assignees.value.find((assignee) => assignee.name === value)) {
    assignees.value.push(obj)
  }
}

watch(assignToMe, (val) => {
  let user = getUser('')
  if (val) {
    addValue(user.name)
  } else {
    removeValue(user.name)
  }
})

watch(
  () => props.open,
  (val) => {
    if (val) {
      oldAssignees.value = [...(assignees.value || [])]

      assignToMe.value = assignees.value.some(
        (assignee) => assignee.name === getUser('').name,
      )
    } else {
      updateAssignees()
    }
  },
  { immediate: true },
)

async function saveReassignment() {
  // Validate reason
  if (!reassignmentReason.value.trim()) {
    showValidationError.value = true
    return
  }
  
  showValidationError.value = false
  isSaving.value = true

  try {
    const removedAssignees = oldAssignees.value
      .filter(
        (assignee) => !assignees.value.find((a) => a.name === assignee.name),
      )
      .map((assignee) => assignee.name)

    const addedAssignees = assignees.value
      .filter(
        (assignee) => !oldAssignees.value.find((a) => a.name === assignee.name),
      )
      .map((assignee) => assignee.name)

    // Remove old assignments
    if (removedAssignees.length) {
      await removeAssignees.submit({
        assignees: removedAssignees,
        reason: reassignmentReason.value,
      })
    }

    // Add new assignments
    if (addedAssignees.length) {
      await addAssignees.submit({
        assignees: addedAssignees,
        reason: reassignmentReason.value,
      })
    }

    // Show success notification
    toast.success(__('Successfully reassigned'))
    
    // Reset form and close modal
    reassignmentReason.value = ''
    emit('close')
    emit('reload')
    
  } catch (error) {
    console.error('Reassignment failed:', error)
    toast.error(__('Failed to reassign. Please try again.'))
  } finally {
    isSaving.value = false
  }
}

const addAssignees = createResource({
  url: 'crm.api.doc.add_assignments_with_reason',
  makeParams: (params) => ({
    doctype: props.doctype,
    name: props.docname,
    assignees: params.assignees,
    reason: params.reason,
  }),
  onSuccess: () => {
    capture('assign_to', { doctype: props.doctype })
  },
})

const removeAssignees = createResource({
  url: 'crm.api.doc.remove_assignments_with_reason',
  makeParams: (params) => ({
    doctype: props.doctype,
    name: props.docname,
    assignees: params.assignees,
    reason: params.reason,
  }),
})
</script>
