const firebaseConfig = {
  apiKey: "AIzaSyCYKCanPFIVqK8TfD0v4p7JB7parMUv4RgT4",
  authDomain: "curriculoiagerador-ef3dc.firebaseapp.com",
  projectId: "curriculoiagerador-ef3dc",
  storageBucket: "curriculoiagerador-ef3dc.firebasestorage.app",
  messagingSenderId: "932941525566",
  appId: "1:932941525566:web:0292df9938d482e6f2576f",
  measurementId: "G-LWL6686HFD"
};

if (!firebase.apps.length) firebase.initializeApp(firebaseConfig);

window.firebaseAuthReady = (async () => {
  const auth = firebase.auth();
  await auth.setPersistence(firebase.auth.Auth.Persistence.LOCAL);
  return auth;
})();
