import type { DiagramSpec } from "./types";
import { firstRobotsCascade, pidCascade } from "./specs/cascade";
import { gitAreas, gitBranches } from "./specs/gitModel";
import { pwmDuty } from "./specs/pwm";
import { hbridgeCurrentPath } from "./specs/hbridge";
import { pullupExternal, pullupInternal } from "./specs/pullup";
import { reactionTimerStates } from "./specs/reactionTimer";
import { ros2GraphSystem } from "./specs/ros2Graph";
import { ros2WorkspaceTree } from "./specs/ros2Workspace";
import { slamTfChain } from "./specs/slamTf";
import { urdfTwoPublishers } from "./specs/urdfPublishers";

/** Every diagram that MDX can show with <Diagram id="..." />. tools/check_diagrams.mjs validates each entry. */
export const DIAGRAMS: Record<string, DiagramSpec> = {
  [pidCascade.id]: pidCascade,
  [firstRobotsCascade.id]: firstRobotsCascade,
  [reactionTimerStates.id]: reactionTimerStates,
  [ros2GraphSystem.id]: ros2GraphSystem,
  [ros2WorkspaceTree.id]: ros2WorkspaceTree,
  [slamTfChain.id]: slamTfChain,
  [urdfTwoPublishers.id]: urdfTwoPublishers,
  [gitAreas.id]: gitAreas,
  [gitBranches.id]: gitBranches,
  [pwmDuty.id]: pwmDuty,
  [hbridgeCurrentPath.id]: hbridgeCurrentPath,
  [pullupInternal.id]: pullupInternal,
  [pullupExternal.id]: pullupExternal,
};
