export const knowledgeApi = {
  listKnowledgeBases: "GET /knowledge-bases",
  createKnowledgeBase: "POST /knowledge-bases",
  getKnowledgeBase: "GET /knowledge-bases/{knowledgeBaseId}",
  updateKnowledgeBase: "PATCH /knowledge-bases/{knowledgeBaseId}",
  deleteKnowledgeBase: "DELETE /knowledge-bases/{knowledgeBaseId}",
  listOptions: "GET /knowledge-bases/options",
  uploadDocument: "POST /knowledge-bases/{knowledgeBaseId}/documents",
  listDocuments: "GET /knowledge-bases/{knowledgeBaseId}/documents",
  getDocument: "GET /knowledge-bases/{knowledgeBaseId}/documents/{documentId}",
  deleteDocument: "DELETE /knowledge-bases/{knowledgeBaseId}/documents/{documentId}",
  reprocessDocument:
    "POST /knowledge-bases/{knowledgeBaseId}/documents/{documentId}/reprocess",
  retrievalTest: "POST /knowledge-bases/{knowledgeBaseId}/retrieval-test",
} as const;
