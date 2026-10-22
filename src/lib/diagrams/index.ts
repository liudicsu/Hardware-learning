import type { DiagramSpec } from "./types";
import { cartPoleSigns } from "./specs/cartPole";
import { gzBridge } from "./specs/gzBridge";
import { firstRobotsCascade, pidCascade } from "./specs/cascade";
import { debounceQuiet } from "./specs/debounce";
import { gitAreas, gitBranches } from "./specs/gitModel";
import { pwmDuty } from "./specs/pwm";
import { i2cWhoAmI } from "./specs/i2c";
import { hbridgeCurrentPath } from "./specs/hbridge";
import { pullupExternal, pullupInternal } from "./specs/pullup";
import { reactionTimerStates } from "./specs/reactionTimer";
import { ros2GraphSystem } from "./specs/ros2Graph";
import { ros2WorkspaceTree } from "./specs/ros2Workspace";
import { nav2Pipeline } from "./specs/nav2Pipeline";
import { slamPoseGraph } from "./specs/slamPoseGraph";
import { stsPackets } from "./specs/sts";
import { slamTfChain } from "./specs/slamTf";
import { urdfTwoPublishers } from "./specs/urdfPublishers";
import { vlaDataflow } from "./specs/vlaDataflow";

/** Every diagram that MDX can show with <Diagram id="..." />. tools/check_diagrams.mjs validates each entry. */
export const DIAGRAMS: Record<string, DiagramSpec> = {
  [pidCascade.id]: pidCascade,
  [firstRobotsCascade.id]: firstRobotsCascade,
  [reactionTimerStates.id]: reactionTimerStates,
  [ros2GraphSystem.id]: ros2GraphSystem,
  [ros2WorkspaceTree.id]: ros2WorkspaceTree,
  [slamTfChain.id]: slamTfChain,
  [slamPoseGraph.id]: slamPoseGraph,
  [urdfTwoPublishers.id]: urdfTwoPublishers,
  [nav2Pipeline.id]: nav2Pipeline,
  [gitAreas.id]: gitAreas,
  [gitBranches.id]: gitBranches,
  [pwmDuty.id]: pwmDuty,
  [hbridgeCurrentPath.id]: hbridgeCurrentPath,
  [pullupInternal.id]: pullupInternal,
  [pullupExternal.id]: pullupExternal,
  [i2cWhoAmI.id]: i2cWhoAmI,
  [debounceQuiet.id]: debounceQuiet,
  [stsPackets.id]: stsPackets,
  [cartPoleSigns.id]: cartPoleSigns,
  [gzBridge.id]: gzBridge,
  [vlaDataflow.id]: vlaDataflow,
};
