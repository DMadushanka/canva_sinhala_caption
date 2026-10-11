import { SubtitleSegment, CaptionStyle } from "../types";

/**
 * Handles communication with the Canva Apps SDK.
 * Supports both Canva runtime (inside Canva iframe) and standalone browser development.
 */
export async function addCaptionToCanva(segment: SubtitleSegment, style: CaptionStyle): Promise<boolean> {
  try:
    // Check if running inside Canva Apps SDK environment
    // @ts-ignore
    if (window.Canva && window.Canva.design) {
      // @ts-ignore
      await window.Canva.design.addNativeElement({
        type: "TEXT",
        children: [segment.text],
        fontFamily: style.fontFamily,
        fontSize: style.fontSize,
        color: style.textColor,
      });
      return true;
    } else {
      console.log("[Canva SDK Sim] Injected Sinhala text into canvas:", segment.text, style);
      return true;
    }
  } catch (err) {
    console.warn("Canva SDK integration notice:", err);
    return false;
  }
}
