import {defineConfig, type Plugin} from 'vite';
import react from '@vitejs/plugin-react';

// React embeds this documentation URL in its production-only error formatter.
// It is never fetched, but remove it from the offline distributable so the
// emitted bundle itself contains no external URL strings.
function offlineDiagnostics(): Plugin {
  return {
    name: 'offline-react-diagnostics',
    generateBundle(_options, bundle) {
      for (const item of Object.values(bundle)) {
        if (item.type === 'chunk') {
          item.code = item.code.replaceAll('https://react.dev/errors/', 'React error #');
        }
      }
    },
  };
}

export default defineConfig({plugins:[react(), offlineDiagnostics()],server:{proxy:{'/api':'http://127.0.0.1:8510'}}});
