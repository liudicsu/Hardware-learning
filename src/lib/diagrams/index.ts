import type { DiagramSpec } from "./types";
import { firstRobotsCascade, pidCascade } from "./specs/cascade";
import { reactionTimerStates } from "./specs/reactionTimer";

/** Every diagram that MDX can show with <Diagram id="..." />. tools/check_diagrams.mjs validates each entry. */
export const DIAGRAMS: Record<string, DiagramSpec> = {
  [pidCascade.id]: pidCascade,
  [firstRobotsCascade.id]: firstRobotsCascade,
  [reactionTimerStates.id]: reactionTimerStates,
};
