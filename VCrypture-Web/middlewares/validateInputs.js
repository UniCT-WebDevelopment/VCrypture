const checkFile = (file) => {
  const acceptedImageTypes = ['image/gif', 'image/jpeg', 'image/png', 'image/bmp', 'image/tiff'];
  return file && acceptedImageTypes.includes(file.mimetype);
};

const checkEmail = (str) => {
  const re = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
  return re.test(String(str).toLowerCase());
};

const checkMode = (mode) => (parseInt(mode, 10) === 1 || parseInt(mode, 10) === 2);

module.exports = (req, res, next) => {
  const { mode, dest } = req.body;

  const modeCheck = checkMode(mode);
  const destCheck = checkEmail(dest);

  if (req.file) {
    const fileCheck = checkFile(req.file);
    if (modeCheck && destCheck && fileCheck) return next();
  } else if (req.files) {
    let fileChecks = true;
    req.files.forEach((f) => {
      fileChecks = fileChecks && checkFile(f);
    });
    if (modeCheck && destCheck && fileChecks) return next();
  }

  const view = req.originalUrl.match(/\/([a-z]+)\/.*/)[1];
  return res.status(400).render(view, { error: 'Invalid inputs!', csrfToken: req.csrfToken() });
};
