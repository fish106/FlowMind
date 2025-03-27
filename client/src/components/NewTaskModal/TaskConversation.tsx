import { ArrowCircleUp28Filled, ArrowCircleUp28Regular, RecordStop28Filled } from '@fluentui/react-icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Textarea } from '@/components/ui/Textarea';
import { WORKFLOW_AI_USERNAME } from '@/lib/constants';
import { cn } from '@/lib/utils';
import { WorkflowAIGradientIcon } from '../Logos/WorkflowAIIcon';
import { SimpleTooltip } from '../ui/Tooltip';
import { GhostLoading } from './GhostLoading';
import { ConversationMessage, TaskConversationMessage, TaskConversationRetryCell } from './TaskConversationMessage';

dayjs.extend(relativeTime);

const DEFAULT_MESSAGE_SUGGESTIONS = [
  'Given a product review, extract the main sentiment.',
  'Extract the city and country from the image.',
  'Summarize a text.',
];

type ActionButtonProps = {
  sendDisabled: boolean;
  onSendIteration: () => void;
  showStop?: boolean;
  onStop?: () => void;
};

function ActionButton(props: ActionButtonProps) {
  const { sendDisabled, onSendIteration, showStop, onStop } = props;

  if (showStop) {
    return (
      <SimpleTooltip content='Stop generating response' tooltipDelay={0} side='top' tooltipClassName='m-1'>
        <RecordStop28Filled className='text-gray-900 cursor-pointer mx-2 my-2' onClick={onStop} />
      </SimpleTooltip>
    );
  }

  if (sendDisabled) {
    return <ArrowCircleUp28Regular className='text-gray-300 cursor-not-allowed mx-2 my-2' />;
  }

  return (
    <ArrowCircleUp28Filled
      className='text-indigo-600 cursor-pointer mx-2 my-2'
      onClick={!sendDisabled ? () => onSendIteration() : undefined}
    />
  );
}

type TaskConversationInputProps = {
  userMessage: string;
  setUserMessage: (message: string) => void;
  onSendIteration: () => Promise<void>;
  autoFocus?: boolean;
  controlYPressed?: () => void;
  controlNPressed?: () => void;
  showStop?: boolean;
  onStop?: () => void;
};

export function TaskConversationInput(props: TaskConversationInputProps) {
  const {
    userMessage,
    setUserMessage,
    onSendIteration,
    autoFocus = true,
    controlYPressed,
    controlNPressed,
    showStop = false,
    onStop,
  } = props;
  const [isFocused, setIsFocused] = useState(false);

  const onMessageChange = useCallback(
    (event: React.ChangeEvent<HTMLTextAreaElement>) => {
      setUserMessage(event.target.value);
    },
    [setUserMessage]
  );

  const onKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        onSendIteration();
      }
      if (event.key === 'y' && event.ctrlKey && !!controlYPressed) {
        event.preventDefault();
        controlYPressed();
      }
      if (event.key === 'n' && event.ctrlKey && !!controlNPressed) {
        event.preventDefault();
        controlNPressed();
      }
    },
    [onSendIteration, controlYPressed, controlNPressed]
  );

  const sendDisabled = !userMessage;

  return (
    <div className='flex w-full h-fit p-4'>
      <div
        className={cn(
          'flex flex-row w-full h-fit justify-between items-end bg-white rounded-[2px] border border-gray-300',
          isFocused ? 'border-[2px] border-gray-900' : 'border-[1px] border-gray-200 p-[1px]'
        )}
      >
        <Textarea
          value={userMessage}
          onChange={onMessageChange}
          placeholder='Type your message here...'
          className='max-h-[300px] font-lato text-[13px] text-gray-900 border-none focus-visible:ring-0 focus:outline-none scrollbar-hide'
          onKeyDown={onKeyDown}
          autoFocus={autoFocus}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
        />

        <ActionButton
          sendDisabled={sendDisabled}
          onSendIteration={onSendIteration}
          showStop={showStop}
          onStop={onStop}
        />
      </div>
    </div>
  );
}

type TaskConversationMessagesProps = {
  messages: ConversationMessage[];
  loading: boolean;
  showRetry: boolean;
  retry: () => void;
  className?: string;
};

export function TaskConversationMessages(props: TaskConversationMessagesProps) {
  const { messages, loading, showRetry, retry, className } = props;
  const scrollRef = useRef<HTMLDivElement>(null);
  const hadMessagesRef = useRef(false);

  useEffect(() => {
    if (scrollRef.current) {
      const isFirstMessages = messages.length > 0 && !hadMessagesRef.current;
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: isFirstMessages ? 'instant' : 'smooth',
      });
      hadMessagesRef.current = messages.length > 0;
    }
  }, [loading, messages]);

  const isStreaming = useMemo(() => messages.some((message) => message.streamed), [messages]);

  return (
    <div ref={scrollRef} className={cn('flex flex-col flex-1 overflow-y-auto px-4 shrink-0', className)}>
      {messages.map((message, index) => (
        <TaskConversationMessage
          key={!!message.date ? dayjs(message.date).format() : index}
          message={message}
          showHeaderForAgent={index === 0 || messages[index - 1].username !== message.username}
        />
      ))}
      {showRetry && <TaskConversationRetryCell retry={retry} />}
      {loading && !isStreaming && (
        <TaskConversationMessage
          message={{
            username: WORKFLOW_AI_USERNAME,
            message: <GhostLoading className='mt-1' />,
          }}
          showHeaderForAgent={messages.length === 0 || messages[messages.length - 1].username !== WORKFLOW_AI_USERNAME}
        />
      )}
    </div>
  );
}

type TaskConversationMessageSuggestionProps = {
  suggestion: string;
  onSendIteration: (suggestion?: string) => Promise<void>;
};

function TaskConversationMessageSuggestion(props: TaskConversationMessageSuggestionProps) {
  const { suggestion, onSendIteration } = props;

  const onClick = useCallback(() => {
    onSendIteration(suggestion);
  }, [onSendIteration, suggestion]);

  return (
    <div
      className='w-[240px] border border-gray-300 bg-white font-normal text-base rounded-[2px] p-4 text-gray-600 hover:bg-gray-100 cursor-pointer transition-colors'
      onClick={onClick}
    >
      {suggestion}
    </div>
  );
}

type TaskConverationGreetingProps = {
  userFirstName?: string | undefined | null;
  onSendIteration: (suggestion?: string) => Promise<void>;
};

function TaskConverationGreeting(props: TaskConverationGreetingProps) {
  const { userFirstName, onSendIteration } = props;
  const greetingMessage = useMemo(
    () => `Hi${userFirstName ? ` ${userFirstName}` : ''}, what do you want to build today?`,
    [userFirstName]
  );
  return (
    <div className='flex-1 flex flex-col justify-center items-center font-lato'>
      <WorkflowAIGradientIcon ratio={3.4} />
      <div className='pt-8 text-center text-gray-700 text-lg font-medium'>{greetingMessage}</div>
      <div className='pt-8 flex gap-3 items-center'>
        {DEFAULT_MESSAGE_SUGGESTIONS.map((suggestion, index) => (
          <TaskConversationMessageSuggestion key={index} suggestion={suggestion} onSendIteration={onSendIteration} />
        ))}
      </div>
    </div>
  );
}

type TaskConversationProps = TaskConversationMessagesProps &
  TaskConversationInputProps & {
    userFirstName?: string | undefined | null;
  };

export function TaskConversation(props: TaskConversationProps) {
  const { userMessage, messages, loading, userFirstName, setUserMessage, onSendIteration, showRetry, retry } = props;

  return (
    <div className='flex flex-col h-full'>
      {messages.length === 0 ? (
        <TaskConverationGreeting userFirstName={userFirstName} onSendIteration={onSendIteration} />
      ) : (
        <TaskConversationMessages messages={messages} loading={loading} showRetry={showRetry} retry={retry} />
      )}
      <TaskConversationInput
        setUserMessage={setUserMessage}
        onSendIteration={onSendIteration}
        userMessage={userMessage}
      />
    </div>
  );
}
