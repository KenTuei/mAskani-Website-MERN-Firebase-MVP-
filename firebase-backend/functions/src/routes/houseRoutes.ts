import * as functions from "firebase-functions";
import * as admin from "firebase-admin";
import express = require("express");
import cors = require("cors");
import { addHouse, getHouses, updateHouse, deleteHouse } from "../services/houseService";

admin.initializeApp();

const app = express();
app.use(cors({ origin: true }));
app.use(express.json());

// Routes
app.post("/houses", async (req, res) => {
  const house = await addHouse(req.body);
  res.status(201).json(house);
});

app.get("/houses", async (req, res) => {
  const houses = await getHouses();
  res.json(houses);
});

app.put("/houses/:id", async (req, res) => {
  const updated = await updateHouse(req.params.id, req.body);
  res.json(updated);
});

app.delete("/houses/:id", async (req, res) => {
  const result = await deleteHouse(req.params.id);
  res.json(result);
});

export const api = functions.https.onRequest(app);
