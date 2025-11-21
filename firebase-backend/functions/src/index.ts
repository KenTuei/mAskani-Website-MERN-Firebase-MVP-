import { setGlobalOptions } from "firebase-functions";
import { onRequest } from "firebase-functions/https";
import * as logger from "firebase-functions/logger";
import { api } from "./routes/houseRoutes";

// Set global options for all functions
setGlobalOptions({ maxInstances: 10 });

// Wrap the Express app (api) with onRequest
export const apiFunction = onRequest(api);

logger.info("House listing API initialized", { structuredData: true });
