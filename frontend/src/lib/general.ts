// formats to Date Long, e.g. October 12, 2026
// also converts to the device's timezone
export const formatDateLong = (date: string): string => {
  return new Intl.DateTimeFormat('en-US', { dateStyle: 'long' }).format(new Date(date));
}

// e.g. October 12, 2026 at 10:00 AM
export const formatDateLongAndTimeShort = (date: string): string => {
  return new Intl.DateTimeFormat('en-US', { dateStyle: 'long', timeStyle: 'short' }).format(new Date(date));
}

export const formatTimeMedium = (date: string): string => {
  return new Intl.DateTimeFormat('en-US', { timeStyle: 'short' }).format(new Date(date));
}

export const calcDateLongTimeMediumRange = (startDate: string, endDate: string): string => {
  return formatDateLongAndTimeShort(startDate) + " - " + formatTimeMedium(endDate);
}
