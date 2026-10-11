import { SubtitleSegment, CaptionStyle } from "../types";

/**
 * Handles communication with the Canva Apps SDK.
 * Supports both Canva runtime (inside Canva iframe) and standalone browser development.
 */
export async function addCaptionToCanva(segment: SubtitleSegment, style: CaptionStyle): Promise<boolean> {
  try {
    const { addElementAtPoint, getDefaultPageDimensions } = await import("@canva/design");
    
    let top = 800;
    let left = 100;
    let width = 800;
    
    try {
      const dimensions = await getDefaultPageDimensions();
      if (dimensions && dimensions.width && dimensions.height) {
        width = Math.min(Math.round(dimensions.width * 0.8), 1200);
        left = Math.round((dimensions.width - width) / 2);
        top = Math.round(dimensions.height * 0.82); // Position near the bottom for video subtitle
      }
    } catch (dimErr) {
      console.warn("Could not retrieve default page dimensions:", dimErr);
    }

    await addElementAtPoint({
      type: "text",
      children: [segment.text],
      top,
      left,
      width,
      textAlign: "center",
      fontWeight: "bold",
      fontSize: style.fontSize || 32,
      color: style.textColor || "#ffffff",
    } as any);

    return true;
  } catch (err) {
    try {
      const { addElementAtCursor } = await import("@canva/design");
      await addElementAtCursor({
        type: "text",
        children: [segment.text],
      } as any);
      return true;
    } catch (cursorErr) {
      console.warn("addElementAtCursor fallback notice:", cursorErr);
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
