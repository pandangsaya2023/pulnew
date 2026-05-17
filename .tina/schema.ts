import { defineConfig, defineSchema } from "tinacms";

const schema = defineSchema({
  collections: [
      {
            name: "post",
                  label: "Posts",
                        path: "content/posts",
                              fields: [
                                      {
                                                type: "string",
                                                          name: "title",
                                                                    label: "Title",
                                                                              isTitle: true,
                                                                                        required: true,
                                                                                                },
                                                                                                        {
                                                                                                                  type: "rich-text",
                                                                                                                            name: "body",
                                                                                                                                      label: "Body",
                                                                                                                                              },
                                                                                                                                                    ],
                                                                                                                                                        },
                                                                                                                                                          ],
                                                                                                                                                          });

                                                                                                                                                          export default defineConfig({
                                                                                                                                                            schema,
                                                                                                                                                              clientId: "PASTE_CLIENT_ID_KAMU",
                                                                                                                                                                token: "dummytoken",
                                                                                                                                                                });