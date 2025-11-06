/**
 * Instance Types Configuration
 * Pricing and metadata for compute/storage/network resources
 *
 * Price Storage Strategy:
 * - Prices stored as integers (multiplied by 100) to maintain precision
 * - Example: ₩166.67 → stored as 16667
 * - This preserves 2 decimal places while avoiding floating-point errors
 * - Use getUnitPrice() for calculations (returns integer in hundredths)
 * - Use getDisplayPrice() for UI display only (returns number, may have FP imprecision)
 */

// ============================================================================
// Instance Type Definitions
// ============================================================================

/**
 * Supported billing units for resources
 */
export type BillingUnit = 'HOURS' | 'GB'

/**
 * Instance Type Configuration
 * Defines resource types with pricing and localized descriptions
 */
export type InstanceTypeConfig = {
  readonly value: string
  readonly label: string
  readonly unit: BillingUnit
  /**
   * Price stored as integer (actual price * 100)
   * Example: ₩397 → 39700, ₩166.67 → 16667
   * Use getUnitPrice() for calculations, getDisplayPrice() for display
   */
  readonly price: number
  readonly description: {
    readonly ko: string
    readonly en: string
  }
}

/**
 * Available instance types with pricing
 * Centralized configuration for easy updates
 */
export const INSTANCE_TYPES: readonly InstanceTypeConfig[] = [
  {
    value: 'compute.c2.c8m8',
    label: 'compute.c2.c8m8 (8 vCPU, 8GB RAM)',
    unit: 'HOURS',
    price: 39700, // 397 * 100 (stored in hundredths)
    description: {
      ko: '일반 컴퓨팅 인스턴스 - ₩397/시간',
      en: 'General compute instance - ₩397/hour',
    },
  },
  {
    value: 'compute.g2.t4.c8m64',
    label: 'compute.g2.t4.c8m64 (GPU T4, 8 vCPU, 64GB RAM)',
    unit: 'HOURS',
    price: 16667, // 166.67 * 100 (stored in hundredths)
    description: {
      ko: 'GPU 인스턴스 - ₩166.67/시간',
      en: 'GPU instance - ₩166.67/hour',
    },
  },
  {
    value: 'storage.volume.ssd',
    label: 'storage.volume.ssd (SSD Storage)',
    unit: 'GB',
    price: 10000, // 100 * 100 (stored in hundredths)
    description: {
      ko: 'SSD 블록 스토리지 - ₩100/GB/월',
      en: 'SSD block storage - ₩100/GB/month',
    },
  },
  {
    value: 'network.floating_ip',
    label: 'network.floating_ip (Floating IP)',
    unit: 'HOURS',
    price: 2500, // 25 * 100 (stored in hundredths)
    description: {
      ko: 'Floating IP - ₩25/시간',
      en: 'Floating IP - ₩25/hour',
    },
  },
]

/**
 * Get instance type configuration by value
 * @param value - Instance type value (e.g., 'compute.c2.c8m8')
 * @returns Instance configuration or undefined
 */
export function getInstanceType(value: string): InstanceTypeConfig | undefined {
  return INSTANCE_TYPES.find(instance => instance.value === value)
}

/**
 * Get instance description in specified language
 * @param value - Instance type value
 * @param locale - Language code ('ko' or 'en')
 * @returns Localized description
 */
export function getInstanceDescription(
  value: string,
  locale: 'ko' | 'en' = 'ko'
): string {
  const instance = getInstanceType(value)
  return instance?.description[locale] ?? ''
}

/**
 * Get display price from stored integer price
 *
 * ⚠️ FOR UI DISPLAY ONLY - NOT FOR CALCULATIONS
 *
 * Divides by 100 to convert stored integer to decimal price.
 * May have floating-point imprecision (e.g., 16667/100 ≠ exactly 166.67).
 * This is acceptable for display purposes.
 *
 * @param value - Instance type value
 * @returns Display price as number (e.g., 397, 166.67) - may have FP imprecision
 *
 * @example
 * getDisplayPrice('compute.c2.c8m8')      // 397
 * getDisplayPrice('compute.g2.t4.c8m64') // 166.67 (may have tiny FP error)
 */
export function getDisplayPrice(value: string): number {
  const instance = getInstanceType(value)
  if (!instance) return 0

  // Convert from hundredths to display value
  // Note: This may introduce floating-point imprecision, which is acceptable for display
  return instance.price / 100
}

/**
 * Get unit price for calculations (in hundredths)
 *
 * ✅ FOR CALCULATIONS - MAINTAINS PRECISION
 *
 * Returns integer price in hundredths to avoid floating-point errors.
 * Use this for all billing calculations, not getDisplayPrice().
 *
 * @param value - Instance type value
 * @returns Integer price in hundredths (e.g., 39700 for ₩397, 16667 for ₩166.67)
 *
 * @example
 * getUnitPrice('compute.c2.c8m8')      // 39700 (₩397 * 100)
 * getUnitPrice('compute.g2.t4.c8m64') // 16667 (₩166.67 * 100)
 */
export function getUnitPrice(value: string): number {
  const instance = getInstanceType(value)
  return instance?.price ?? 0
}
