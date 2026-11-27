// cd backend && uv run quickticket openapi > quickticket.json
// bun run orval
// https://orval.dev/docs/guides/react-query
import { defineConfig } from 'orval';

export default defineConfig({
  quickticket: {
    output: {
      target: 'src/api/quickticket.ts',
      client: 'react-query',
      schemas: 'src/api/model',
      mode: 'tags-split',
      // Since we have a custom axios client, we don't need base URL here
      // baseUrl: {
      //   runtime: 'import.meta.env.VITE_API_URL',
      // },
      // https://orval.dev/docs/reference/configuration/output#mock
      // mock: true,
      tagsSplitDeduplication: true,
      clean: true,
      // formatter: 'biome',
      // https://orval.dev/docs/guides/custom-axios/
      httpClient: 'axios',
      override: {
        mutator: {
          path: 'src/lib/api.ts',
          name: 'api',
        },
        // https://orval.dev/docs/reference/configuration/output#type-generation-options
        useDates: true,
        useBigInt: true,
        useBrandedTypes: true, // NewType
        useNamedParameters: true,
        useDeprecatedOperations: false,
      },
    },
    input: {
      target: './quickticket.json',
    },
  },
});
