// cd backend && uv run quickticket openapi > quickticket.json
// bun run orval
// https://orval.dev/docs/guides/react-query
import { defineConfig } from 'orval';

export default defineConfig({
  quickticket: {
    output: {
      mode: 'tags-split',
      target: 'src/api/quickticket.ts',
      schemas: 'src/api/model',
      client: 'react-query',
      mock: true,
      // https://orval.dev/docs/guides/custom-axios/
      httpClient: 'axios',
      override: {
        mutator: {
          path: 'src/lib/api.ts',
          name: 'api',
        },
      },
    },
    input: {
      target: './quickticket.json',
    },
  },
});
