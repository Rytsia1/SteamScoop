export interface User {
  id: string;
  email: string;
  display_name: string;
  status: string;
  roles: string[];
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  email: string;
  password: string;
  display_name: string;
}

export interface LoginResponseData {
  user: User;
  token: string;
}

