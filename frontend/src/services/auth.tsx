import {createContext,useContext,type ReactNode} from 'react';
import {useQuery} from '@tanstack/react-query';
import {api,type User} from './api';
const Context=createContext<{user?:User;loading:boolean;refresh:()=>void}>({loading:true,refresh:()=>{}});
export function AuthProvider({children}:{children:ReactNode}){const q=useQuery({queryKey:['me'],queryFn:()=>api<User>('auth/me/'),retry:false});return <Context.Provider value={{user:q.data,loading:q.isPending,refresh:()=>{q.refetch()}}}>{children}</Context.Provider>}
export const useAuth=()=>useContext(Context);
