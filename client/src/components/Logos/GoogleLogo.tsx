type GoogleLogoProps = {
  ratio?: number;
  className?: string;
};

export function GoogleLogo(props: GoogleLogoProps) {
  const { ratio = 1, className = '' } = props;
  const width = 108 * ratio;
  const height = 36 * ratio;
  return (
    <svg
      width={width}
      height={height}
      className={className}
      viewBox='0 0 108 36'
      fill='none'
      xmlns='http://www.w3.org/2000/svg'
    >
      <g clipPath='url(#clip0_3479_8334)'>
        <path
          d='M45.8779 18.462C45.8779 23.4589 41.9688 27.1411 37.1714 27.1411C32.374 27.1411 28.4648 23.4589 28.4648 18.462C28.4648 13.4298 32.374 9.78284 37.1714 9.78284C41.9688 9.78284 45.8779 13.4298 45.8779 18.462ZM42.0666 18.462C42.0666 15.3394 39.8009 13.2028 37.1714 13.2028C34.5418 13.2028 32.2761 15.3394 32.2761 18.462C32.2761 21.5533 34.5418 23.7211 37.1714 23.7211C39.8009 23.7211 42.0666 21.5494 42.0666 18.462Z'
          fill='#94A3B8'
        />
        <path
          d='M64.663 18.462C64.663 23.4589 60.7539 27.1411 55.9565 27.1411C51.1591 27.1411 47.25 23.4589 47.25 18.462C47.25 13.4337 51.1591 9.78284 55.9565 9.78284C60.7539 9.78284 64.663 13.4298 64.663 18.462ZM60.8517 18.462C60.8517 15.3394 58.5861 13.2028 55.9565 13.2028C53.327 13.2028 51.0613 15.3394 51.0613 18.462C51.0613 21.5533 53.327 23.7211 55.9565 23.7211C58.5861 23.7211 60.8517 21.5494 60.8517 18.462Z'
          fill='#94A3B8'
        />
        <path
          d='M82.6617 10.3072V25.8889C82.6617 32.2985 78.8817 34.9163 74.413 34.9163C70.2065 34.9163 67.6747 32.1028 66.72 29.802L70.0382 28.4207C70.6291 29.8333 72.0769 31.5002 74.4091 31.5002C77.2695 31.5002 79.0421 29.7354 79.0421 26.4133V25.165H78.9091C78.056 26.2176 76.4126 27.1372 74.3387 27.1372C69.9991 27.1372 66.0234 23.3572 66.0234 18.4933C66.0234 13.5941 69.9991 9.78284 74.3387 9.78284C76.4087 9.78284 78.0521 10.7024 78.9091 11.7237H79.0421V10.3111H82.6617V10.3072ZM79.3121 18.4933C79.3121 15.4372 77.2734 13.2028 74.6791 13.2028C72.0495 13.2028 69.8465 15.4372 69.8465 18.4933C69.8465 21.5181 72.0495 23.7211 74.6791 23.7211C77.2734 23.7211 79.3121 21.5181 79.3121 18.4933Z'
          fill='#94A3B8'
        />
        <path
          d='M88.6275 1.17346V26.6082H84.9102V1.17346H88.6275Z'
          fill='#94A3B8'
        />
        <path
          d='M103.116 21.3175L106.074 23.2897C105.12 24.7023 102.819 27.1362 98.8431 27.1362C93.9126 27.1362 90.2305 23.3249 90.2305 18.4571C90.2305 13.2958 93.9439 9.77795 98.4166 9.77795C102.92 9.77795 105.124 13.3623 105.844 15.2993L106.239 16.2853L94.6366 21.0906C95.5248 22.8319 96.9061 23.7201 98.8431 23.7201C100.784 23.7201 102.13 22.7653 103.116 21.3175ZM94.0105 18.1949L101.766 14.9745C101.34 13.8906 100.056 13.1353 98.5457 13.1353C96.6087 13.1353 93.9126 14.8453 94.0105 18.1949Z'
          fill='#94A3B8'
        />
        <path
          d='M14.3948 16.2044V12.5223H26.8031C26.9244 13.164 26.987 13.9231 26.987 14.7449C26.987 17.5075 26.2318 20.9236 23.7979 23.3575C21.4305 25.8227 18.4057 27.1375 14.3987 27.1375C6.97178 27.1375 0.726562 21.0879 0.726562 13.661C0.726562 6.23401 6.97178 0.184448 14.3987 0.184448C18.5074 0.184448 21.4344 1.79662 23.6335 3.89793L21.0353 6.49619C19.4583 5.01706 17.3218 3.86662 14.3948 3.86662C8.97134 3.86662 4.72961 8.23749 4.72961 13.661C4.72961 19.0844 8.97134 23.4553 14.3948 23.4553C17.9126 23.4553 19.9161 22.0427 21.1996 20.7592C22.2405 19.7184 22.9253 18.2314 23.1953 16.2005L14.3948 16.2044Z'
          fill='#94A3B8'
        />
      </g>
      <defs>
        <clipPath id='clip0_3479_8334'>
          <rect
            width='106.435'
            height='36'
            fill='white'
            transform='translate(0.585938)'
          />
        </clipPath>
      </defs>
    </svg>
  );
}
