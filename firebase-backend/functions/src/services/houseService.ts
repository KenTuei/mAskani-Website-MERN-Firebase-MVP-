import { firestore } from "firebase-admin";

export interface House {
  id?: string;
  createdAt?: firestore.Timestamp;
  // add other known house properties here as needed, or allow arbitrary props:
  [key: string]: any;
}

const db = firestore();

export const addHouse = async (house: House) => {
  const docRef = db.collection("houses").doc();
  house.id = docRef.id;
  house.createdAt = firestore.Timestamp.now();
  await docRef.set(house);
  return house;
};

export const getHouses = async () => {
  const snapshot = await db.collection("houses").orderBy("createdAt", "desc").get();
  return snapshot.docs.map(doc => doc.data());
};

export const updateHouse = async (id: string, data: Partial<House>) => {
  const docRef = db.collection("houses").doc(id);
  await docRef.update(data);
  return { id, ...data };
};

export const deleteHouse = async (id: string) => {
  await db.collection("houses").doc(id).delete();
  return { success: true };
};
