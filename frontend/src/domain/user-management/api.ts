export const userManagementApi = {
  listUsers: "GET /users",
  getUserDetail: "GET /users/{userId}",
  createUser: "POST /users",
  updateUser: "PUT /users/{userId}",
  enableUser: "POST /users/{userId}/enable",
  disableUser: "POST /users/{userId}/disable",
  resetPassword: "POST /users/{userId}/reset-password",
  deleteUser: "DELETE /users/{userId}",
} as const;
