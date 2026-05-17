import { defineConfig } from "tinacms";

export default defineConfig({
  clientId: "masukin-client-id-di-sini",
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
