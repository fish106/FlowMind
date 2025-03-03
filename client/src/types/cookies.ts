// Using a custom type for CookieStore since it looks like Next.js is not exporting it
export interface CookieStore {
  get(name: string): { value: string } | undefined;
  set(
    name: string,
    value: string,
    options: {
      maxAge: number;
      path: string;
      secure: boolean;
      sameSite: 'strict' | 'lax' | 'none';
      httpOnly: boolean;
    }
  ): void;
}
