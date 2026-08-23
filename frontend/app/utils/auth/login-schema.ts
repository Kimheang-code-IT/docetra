import { z } from 'zod'

export function createLoginSchema(emailRequired: string, passwordRequired: string) {
  return z.object({
    email: z.email({ error: emailRequired }),
    password: z.string().min(6, { error: passwordRequired }),
  })
}

export function createSetupSchema(messages: {
  emailRequired: string
  nameRequired: string
  passwordTooShort: string
  passwordMismatch: string
}) {
  return z.object({
    name: z.string().trim().min(1, { error: messages.nameRequired }),
    email: z.email({ error: messages.emailRequired }),
    password: z.string().min(8, { error: messages.passwordTooShort }),
    passwordConfirmation: z.string().min(1, { error: messages.passwordMismatch }),
  }).refine(data => data.password === data.passwordConfirmation, {
    message: messages.passwordMismatch,
    path: ['passwordConfirmation'],
  })
}
