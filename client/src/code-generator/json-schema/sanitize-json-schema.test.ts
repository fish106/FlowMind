import { JsonSchema } from '@/types';
import { sanitize } from './sanitize-json-schema';

describe('Sanitize JSON schema', () => {
  describe('object', () => {
    it('should add object type at root if properties is present', () => {
      const sane = sanitize({
        properties: {
          rephrased_comment: {
            description: 'The rephrased comment',
            type: 'string',
            examples: ['This is a rephrased example comment.', 'Another rephrased example tweet.'],
          },
        },
        required: ['rephrased_comment'],
      });

      expect(sane).toStrictEqual({
        type: 'object',
        properties: {
          rephrased_comment: {
            type: 'string',
            examples: ['This is a rephrased example comment.', 'Another rephrased example tweet.'],
          },
        },
        required: ['rephrased_comment'],
      });
    });

    it('should add object type recursively if properties is present', () => {
      const sane = sanitize({
        type: 'object',
        properties: {
          key1: {
            properties: {
              key11: {
                properties: {
                  key111: {
                    type: 'string',
                  },
                },
              },
              key12: {
                properties: {
                  key121: {
                    type: 'string',
                  },
                },
              },
            },
          },
          key2: {
            properties: {
              key21: {
                properties: {
                  key211: {
                    type: 'string',
                  },
                },
              },
              key22: {
                properties: {
                  key221: {
                    type: 'string',
                  },
                },
              },
            },
          },
        },
      });

      expect(sane).toStrictEqual({
        type: 'object',
        properties: {
          key1: {
            type: 'object',
            properties: {
              key11: {
                type: 'object',
                properties: {
                  key111: {
                    type: 'string',
                  },
                },
              },
              key12: {
                type: 'object',
                properties: {
                  key121: {
                    type: 'string',
                  },
                },
              },
            },
          },
          key2: {
            type: 'object',
            properties: {
              key21: {
                type: 'object',
                properties: {
                  key211: {
                    type: 'string',
                  },
                },
              },
              key22: {
                type: 'object',
                properties: {
                  key221: {
                    type: 'string',
                  },
                },
              },
            },
          },
        },
      });
    });

    it('should add object type if patternProperties is present', () => {
      const sane = sanitize({
        patternProperties: {
          '^S_': { type: 'string' },
          '^I_': { type: 'integer' },
        },
      });

      expect(sane).toStrictEqual({
        type: 'object',
        patternProperties: {
          '^S_': { type: 'string' },
          '^I_': { type: 'integer' },
        },
      });
    });

    it('should add object type if propertyNames is present', () => {
      const sane = sanitize({
        propertyNames: {
          pattern: '^[A-Za-z_][A-Za-z0-9_]*$',
        },
      } as JsonSchema);

      expect(sane).toStrictEqual({
        type: 'object',
        propertyNames: {
          pattern: '^[A-Za-z_][A-Za-z0-9_]*$',
        },
      });
    });
  });

  describe('array', () => {
    it('should add array type at root if items are present', () => {
      const sane = sanitize({
        items: {
          type: 'number',
        },
      } as JsonSchema);

      expect(sane).toStrictEqual({
        type: 'array',
        items: {
          type: 'number',
        },
      });
    });

    it('should add array type recursively if items are present', () => {
      const sane = sanitize({
        type: 'array',
        items: {
          items: {
            items: {
              items: {
                type: 'number',
              },
            },
          },
        },
      } as JsonSchema);

      expect(sane).toStrictEqual({
        type: 'array',
        items: {
          type: 'array',
          items: {
            type: 'array',
            items: {
              type: 'array',
              items: {
                type: 'number',
              },
            },
          },
        },
      });
    });

    it('should add array type if prefixItems are present', () => {
      const sane = sanitize({
        prefixItems: [
          { type: 'number' },
          { type: 'string' },
          { enum: ['Street', 'Avenue', 'Boulevard'] },
          { enum: ['NW', 'NE', 'SW', 'SE'] },
        ],
      } as JsonSchema);

      expect(sane).toStrictEqual({
        type: 'array',
        prefixItems: [
          { type: 'number' },
          { type: 'string' },
          { enum: ['Street', 'Avenue', 'Boulevard'] },
          { enum: ['NW', 'NE', 'SW', 'SE'] },
        ],
      });
    });

    it('should add array type if contains is present', () => {
      const sane = sanitize({
        contains: {
          type: 'number',
        },
      } as JsonSchema);

      expect(sane).toStrictEqual({
        type: 'array',
        contains: {
          type: 'number',
        },
      });
    });

    it('should add array type if minItems is present', () => {
      const sane = sanitize({
        minItems: 3,
      } as JsonSchema);

      expect(sane).toStrictEqual({
        type: 'array',
        minItems: 3,
      });
    });

    it('should add array type if maxItems is present', () => {
      const sane = sanitize({
        maxItems: 3,
      } as JsonSchema);

      expect(sane).toStrictEqual({
        type: 'array',
        maxItems: 3,
      });
    });

    it('should add array type if uniqueItems is present', () => {
      const sane = sanitize({
        uniqueItems: true,
      } as JsonSchema);

      expect(sane).toStrictEqual({
        type: 'array',
        uniqueItems: true,
      });
    });
  });
});
