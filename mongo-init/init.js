db = db.getSiblingDB("gridlabd");

db.createUser({
  user: "appuser",
  pwd: "apppassword",
  roles: [{ role: "readWrite", db: "gridlabd" }]
});

db.mycollection.insertOne({ initialized: true, createdAt: new Date() });
