db = db.getSiblingDB("external_jobs");

db.createUser({
  user: "external_jobs",
  pwd: "external_jobs",
  roles: [
    {
      role: "readWrite",
      db: "external_jobs",
    },
  ],
});
