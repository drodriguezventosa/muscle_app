/** Day helpers shared by the calendar views. All dates are ISO days (YYYY-MM-DD). */

/** An ISO day from a Date, in the viewer's own timezone rather than UTC. */
export function isoDay(date: Date): string {
  return new Date(date.getTime() - date.getTimezoneOffset() * 60_000).toISOString().slice(0, 10)
}

export function todayISO(): string {
  return isoDay(new Date())
}

/** The Monday of the week a day belongs to. */
export function startOfWeek(day: string): string {
  const date = new Date(`${day}T00:00:00`)
  // getDay() is 0 for Sunday, which belongs to the week that started six days earlier.
  const weekday = (date.getDay() + 6) % 7
  date.setDate(date.getDate() - weekday)
  return isoDay(date)
}

export function addDays(day: string, days: number): string {
  const date = new Date(`${day}T00:00:00`)
  date.setDate(date.getDate() + days)
  return isoDay(date)
}
