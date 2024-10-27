// src/theme.js
import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  typography: {
    fontFamily: '"Montserrat", sans-serif', // Set your default font family here
  },
  palette: {
    text: {
      primary: '#ffffff', // Set primary text color globally
    },
  },
});

export default theme;
