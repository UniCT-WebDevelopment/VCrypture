const router = require('express').Router();
const csurf = require('csurf');
const fetch = require('node-fetch');
const multer = require('multer');
const FormData = require('form-data');
const { apiEndpoint } = require('../config').app;
const validateInputs = require('../middlewares/validateInputs');

// Set Multer memory storage
const storage = multer.memoryStorage();
const upload = multer({ storage });

const csrfProtection = csurf();

router.get('/', csrfProtection, (req, res) => {
  res.render('taghaddoslatif', { csrfToken: req.csrfToken() });
});

router.post('/enc', upload.single('image'), csrfProtection, validateInputs, async (req, res) => {
  const { dest } = req.body;
  const { buffer, originalname } = req.file;

  const form = new FormData();
  form.append('dest', dest);
  form.append('image', buffer, originalname);

  const options = {
    method: 'POST',
    body: form,
    headers: form.getHeaders()
  };

  const response = await fetch(`${apiEndpoint}/taghaddoslatif`, options);
  const json = await response.json();
  const msg = response.status === 200 ? `Success, email sent to ${json.dest}` : 'Error';
  return res.render('taghaddoslatif', { msg, csrfToken: req.csrfToken() });
});

router.post('/dec', upload.array('share', 2), csrfProtection, validateInputs, async (req, res) => {
  const { mode, dest } = req.body;
  const [share1, share2] = req.files;

  const form = new FormData();
  form.append('dest', dest);
  form.append('mode', mode);
  form.append('share1', share1.buffer, share1.originalname);
  form.append('share2', share2.buffer, share2.originalname);

  const options = {
    method: 'POST',
    body: form,
    headers: form.getHeaders()
  };

  const response = await fetch(`${apiEndpoint}/taghaddoslatif/dec`, options);
  const json = await response.json();
  const msg = response.status === 200 ? `Success, email sent to ${json.dest}` : 'Error';
  return res.render('taghaddoslatif', { msg, csrfToken: req.csrfToken() });
});

module.exports = router;
