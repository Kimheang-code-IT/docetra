export const ACTION_COL_WIDTH = 72
export const ACTION_HEADER = 'ការកំណត់'

/** Khmer labels for all report table headers */
export const TABLE_HEADERS = {
  rank: 'ល.រ.',
  name: 'ឈ្មោះ',
  role: 'តួនាទី',
  email: 'អ៊ីមែល',
  password: 'ពាក្យសម្ងាត់',
  lastLogin: 'ម៉ោងចូលចុងក្រោយ',
  pageAccess: 'ការចូលដំណើរការទំព័រ',
  typeAction: 'ប្រភេទសកម្មភាព',
  username: 'ឈ្មោះអ្នកប្រើ',
  date: 'កាលបរិច្ឆេទ',
  description: 'ការពិពណ៌នា',
  fileName: 'ឈ្មោះឯកសារ',
  type: 'ប្រភេទ',
  size: 'ទំហំ',
  importedAt: 'ម៉ោងការនាំចូល',
  currency: 'រូបិយប័ណ្ណ',
  unitPerCurrency: 'ឯកតាជាចំនួនទឹកប្រាក់',
  rateKhr: 'អត្រាប្តូររូបិយប័ណ្ណជារៀល',
  interMme: 'ក្រសួងរ៉ែ និងថាមពល',
  interMef: 'ក្រសួងសេដ្ឋកិច្ជ និងហិរញ្ញវត្ថុ',
} as const

/** Sub-column width — matches kind-total-revenue category columns */
export const REPORT_SUB_COL_WIDTH = 84

/** Narrow width for short repeated labels (អនុគណនី, currency) */
export const REPORT_NARROW_COL_WIDTH = 64

export type ReportColumn = {
  key: string
  label: string
  width: number
  text?: boolean
  numeric?: boolean
}

/** @deprecated use ReportColumn */
export type SimpleReportColumn = ReportColumn
