// Strips any non-printable-ASCII as the user types.
// Allows: space through tilde, plus newline/tab/CR for textareas.
export function asciiOnly(value: string): string {
  return value.replace(/[^\x20-\x7E\n\r\t]/g, '');
}
