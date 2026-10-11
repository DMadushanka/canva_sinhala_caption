import { SubtitleSegment, CaptionStyle } from "../types";

/**
 * Handles communication with the Canva Apps SDK.
 * Supports both Canva runtime (inside Canva iframe) and standalone browser development.
 */
export async function addCaptionToCanva(segment: SubtitleSegment, style: CaptionStyle): Promise<boolean> {
  try {
    const { addNativeElement } = await import("@canva/design");
    await addNativeElement({
      type: "text" as const,
      children: [segment.text],
    } as any);
    return true;
  } catch (err) {
    try {
      // @ts-ignore
      if (window.Canva && window.Canva.design) {
        // @ts-ignore
        await window.Canva.design.addNativeElement({
          type: "text",
          children: [segment.text],
        });
        return true;
      }
    } catch (fallbackErr) {
      console.warn("Canva SDK fallback notice:", fallbackErr);
    }
    console.warn("Canva SDK notice:", err);
    return false;
  }
}

export async function addAllCaptionsToCanva(segments: SubtitleSegment[], style: CaptionStyle): Promise<number> {
  let added = 0;
  for (const seg of segments) {
    const ok = await addCaptionToCanva(seg, style);
    if (ok) added++;
  }
  return added;
}
