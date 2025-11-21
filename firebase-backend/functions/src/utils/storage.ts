import { getStorage } from "firebase-admin/storage";
import { v4 as uuidv4 } from "uuid";

const bucket = getStorage().bucket();

export const uploadImage = async (file: Buffer, filename: string, contentType: string) => {
  const uniqueName = `${uuidv4()}-${filename}`;
  const fileRef = bucket.file(uniqueName);

  await fileRef.save(file, {
    metadata: { contentType },
    public: true,
  });

  return `https://storage.googleapis.com/${bucket.name}/${uniqueName}`;
};
