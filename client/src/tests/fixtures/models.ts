import { ModelResponse } from '@/types/workflowAI';

export const someNewUnknownModel: ModelResponse = {
  id: 'some-new-unknown-model',
  name: 'Some New Unknown Model',
  icon_url: 'icon_url',
  modes: ['text', 'images'],
  is_not_supported_reason: null,
  average_cost_per_run_usd: 0.1,
  is_latest: false,
  providers: ['fireworks'],
  metadata: {
    quality_index: 100,
    price_per_input_token_usd: 100,
    price_per_output_token_usd: 100,
    release_date: '2024-04-09',
    context_window_tokens: 1000000,
    provider_name: 'some-new-unknown-provider',
  },
};

export const fixtureModels: ModelResponse[] = [
  {
    id: 'gpt-4-turbo-2024-04-09',
    name: 'GPT 4 Turbo 2024 04 09',
    icon_url: 'icon_url',
    modes: ['text', 'images'],
    is_not_supported_reason: null,
    average_cost_per_run_usd: 0.1,
    is_latest: true,
    providers: ['fireworks'],
    metadata: {
      quality_index: 100,
      price_per_input_token_usd: 100,
      price_per_output_token_usd: 100,
      release_date: '2024-04-09',
      context_window_tokens: 1000000,
      provider_name: 'some-new-unknown-provider',
    },
  },
  {
    id: 'gpt-4-0125-preview',
    name: 'GPT 4 0125 Preview',
    icon_url: 'icon_url',
    modes: ['text'],
    is_not_supported_reason: null,
    average_cost_per_run_usd: 0.1,
    is_latest: false,
    providers: ['fireworks'],
    metadata: {
      quality_index: 100,
      price_per_input_token_usd: 100,
      price_per_output_token_usd: 100,
      release_date: '2024-04-09',
      context_window_tokens: 1000000,
      provider_name: 'some-new-unknown-provider',
    },
  },
  {
    id: 'gpt-4-1106-preview',
    name: 'GPT 4 1106 Preview',
    icon_url: 'icon_url',
    modes: ['text'],
    is_not_supported_reason: null,
    average_cost_per_run_usd: 0.1,
    is_latest: false,
    providers: ['fireworks'],
    metadata: {
      quality_index: 100,
      price_per_input_token_usd: 100,
      price_per_output_token_usd: 100,
      release_date: '2024-04-09',
      context_window_tokens: 1000000,
      provider_name: 'some-new-unknown-provider',
    },
  },
  {
    id: 'gpt-4-1106-vision-preview',
    name: 'GPT 4 1106 Vision Preview',
    icon_url: 'icon_url',
    modes: ['text', 'images'],
    is_not_supported_reason: null,
    average_cost_per_run_usd: 0.1,
    is_latest: false,
    providers: ['fireworks'],
    metadata: {
      quality_index: 100,
      price_per_input_token_usd: 100,
      price_per_output_token_usd: 100,
      release_date: '2024-04-09',
      context_window_tokens: 1000000,
      provider_name: 'some-new-unknown-provider',
    },
  },
  {
    id: 'gpt-4-0613',
    name: 'GPT 4 0613',
    icon_url: 'icon_url',
    modes: ['text'],
    is_not_supported_reason: null,
    average_cost_per_run_usd: 0.1,
    is_latest: false,
    providers: ['fireworks'],
    metadata: {
      quality_index: 100,
      price_per_input_token_usd: 100,
      price_per_output_token_usd: 100,
      release_date: '2024-04-09',
      context_window_tokens: 1000000,
      provider_name: 'some-new-unknown-provider',
    },
  },
  {
    id: 'gpt-4-32k-0613',
    name: 'GPT 4 32K 0613',
    icon_url: 'icon_url',
    modes: ['text'],
    is_not_supported_reason: null,
    average_cost_per_run_usd: 0.1,
    is_latest: false,
    providers: ['fireworks'],
    metadata: {
      quality_index: 100,
      price_per_input_token_usd: 100,
      price_per_output_token_usd: 100,
      release_date: '2024-04-09',
      context_window_tokens: 1000000,
      provider_name: 'some-new-unknown-provider',
    },
  },
  {
    id: 'gpt-3.5-turbo-0125',
    name: 'GPT 3.5 Turbo 0125',
    icon_url: 'icon_url',
    modes: ['text'],
    is_not_supported_reason: null,
    average_cost_per_run_usd: 0.1,
    is_latest: false,
    providers: ['fireworks'],
    metadata: {
      quality_index: 100,
      price_per_input_token_usd: 100,
      price_per_output_token_usd: 100,
      release_date: '2024-04-09',
      context_window_tokens: 1000000,
      provider_name: 'some-new-unknown-provider',
    },
  },
  {
    id: 'gpt-3.5-turbo-1106',
    name: 'GPT 3.5 Turbo 1106',
    icon_url: 'icon_url',
    modes: ['text'],
    is_not_supported_reason: null,
    average_cost_per_run_usd: 0.1,
    is_latest: false,
    providers: ['fireworks'],
    metadata: {
      quality_index: 100,
      price_per_input_token_usd: 100,
      price_per_output_token_usd: 100,
      release_date: '2024-04-09',
      context_window_tokens: 1000000,
      provider_name: 'some-new-unknown-provider',
    },
  },
  {
    id: 'claude-3-sonnet-20240229',
    name: 'Claude 3 Sonnet 20240229',
    icon_url: 'icon_url',
    modes: [],
    is_not_supported_reason: null,
    average_cost_per_run_usd: 0.1,
    is_latest: false,
    providers: ['fireworks'],
    metadata: {
      quality_index: 100,
      price_per_input_token_usd: 100,
      price_per_output_token_usd: 100,
      release_date: '2024-04-09',
      context_window_tokens: 1000000,
      provider_name: 'some-new-unknown-provider',
    },
  },
  {
    id: 'claude-3-haiku-20240307',
    name: 'Claude 3 Haiku 20240307',
    icon_url: 'icon_url',
    modes: [],
    is_not_supported_reason: null,
    average_cost_per_run_usd: 0.1,
    is_latest: false,
    providers: ['fireworks'],
    metadata: {
      quality_index: 100,
      price_per_input_token_usd: 100,
      price_per_output_token_usd: 100,
      release_date: '2024-04-09',
      context_window_tokens: 1000000,
      provider_name: 'some-new-unknown-provider',
    },
  },
  {
    id: 'llama3-70b-8192',
    name: 'Llama3 70B 8192',
    icon_url: 'icon_url',
    modes: ['text'],
    is_not_supported_reason: null,
    average_cost_per_run_usd: 0.1,
    is_latest: false,
    providers: ['fireworks'],
    metadata: {
      quality_index: 100,
      price_per_input_token_usd: 100,
      price_per_output_token_usd: 100,
      release_date: '2024-04-09',
      context_window_tokens: 1000000,
      provider_name: 'some-new-unknown-provider',
    },
  },
  {
    id: 'llama3-8b-8192',
    name: 'Llama3 8B 8192',
    icon_url: 'icon_url',
    modes: ['text'],
    is_not_supported_reason: null,
    average_cost_per_run_usd: 0.1,
    is_latest: false,
    providers: ['fireworks'],
    metadata: {
      quality_index: 100,
      price_per_input_token_usd: 100,
      price_per_output_token_usd: 100,
      release_date: '2024-04-09',
      context_window_tokens: 1000000,
      provider_name: 'some-new-unknown-provider',
    },
  },
  {
    id: 'mixtral-8x7b-32768',
    name: 'Mixtral 8X7B 32768',
    icon_url: 'icon_url',
    modes: ['text'],
    is_not_supported_reason: null,
    average_cost_per_run_usd: 0.1,
    is_latest: false,
    providers: ['fireworks'],
    metadata: {
      quality_index: 100,
      price_per_input_token_usd: 100,
      price_per_output_token_usd: 100,
      release_date: '2024-04-09',
      context_window_tokens: 1000000,
      provider_name: 'some-new-unknown-provider',
    },
  },
  {
    id: 'gemini-1.5-pro-preview-0409',
    name: 'Gemini 1.5 Pro Preview 0409',
    icon_url: 'icon_url',
    modes: ['images'],
    is_not_supported_reason: null,
    average_cost_per_run_usd: 0.1,
    is_latest: false,
    providers: ['fireworks'],
    metadata: {
      quality_index: 100,
      price_per_input_token_usd: 100,
      price_per_output_token_usd: 100,
      release_date: '2024-04-09',
      context_window_tokens: 1000000,
      provider_name: 'some-new-unknown-provider',
    },
  },
  {
    id: 'gemini-1.0-pro-vision-001',
    name: 'Gemini 1.0 Pro Vision 001',
    icon_url: 'icon_url',
    modes: ['images'],
    is_not_supported_reason: null,
    average_cost_per_run_usd: 0.1,
    is_latest: false,
    providers: ['fireworks'],
    metadata: {
      quality_index: 100,
      price_per_input_token_usd: 100,
      price_per_output_token_usd: 100,
      release_date: '2024-04-09',
      context_window_tokens: 1000000,
      provider_name: 'some-new-unknown-provider',
    },
  },
  {
    id: 'mistral-large-2-2407',
    name: 'Mistal Large 2 (24.07)',
    icon_url: 'icon_url',
    modes: ['text'],
    is_not_supported_reason: null,
    average_cost_per_run_usd: 0.1,
    is_latest: false,
    providers: ['fireworks'],
    metadata: {
      quality_index: 100,
      price_per_input_token_usd: 100,
      price_per_output_token_usd: 100,
      release_date: '2024-04-09',
      context_window_tokens: 1000000,
      provider_name: 'some-new-unknown-provider',
    },
  },
];
