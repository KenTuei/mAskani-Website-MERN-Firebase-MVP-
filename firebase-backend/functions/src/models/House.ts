export interface House {
    id?: string;
    title: string;
    description: string;
    price: number;
    location: string;
    imageUrl?: string;
    createdAt: FirebaseFirestore.Timestamp;
}
