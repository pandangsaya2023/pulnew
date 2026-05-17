import { defineConfig } from "tinacms";

export default defineConfig({
  clientId: "9dc141ca-bc40-4de9-a81e-852fc0cbdebb",
  token: "masukin-token-di-sini",
  branch: "main",
  schema: {
    collections: [
      {
        name: "posts",
        label: "Posts",
        path: "content/posts",
        format: "md",
        fields: [
          { type: "string", name: "title", label: "Title", isTitle: true, required: true },
          { type: "datetime", name: "date", label: "Date" },
          { type: "string", name: "category", label: "Category", options: ["Politik", "Ekonomi", "Hiburan"] },
          { type: "image", name: "image", label: "Gambar" },
          { type: "rich-text", name: "body", label: "Isi", isBody: true },
        ],
      },
    ],
  },
});
