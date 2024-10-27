import React from 'react';
import './App.css';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import LandingPage from './Components/LandingPage';
import theme from './theme';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <div className="App" style={{ backgroundColor: '#05070A', minHeight: '100vh' }}>
        <LandingPage />
      </div>
    </ThemeProvider>
  );
}

export default App;