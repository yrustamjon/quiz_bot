import {useState} from 'react';
import {NavLink,Outlet,Navigate,useLocation} from 'react-router-dom';
import {useQueryClient} from '@tanstack/react-query';
import {GraduationCap,LayoutDashboard,BookOpen,Users,FileQuestion,Trophy,BarChart3,Settings,Menu,LogOut,PanelLeftClose} from 'lucide-react';
import {useAuth} from '../services/auth';
import {post} from '../services/api';
import {ThemeToggle} from '../components/theme';
import {Modal} from '../components/ui/dialog';
import {Loading} from '../components/states';
export default function Shell(){const {user,loading,refresh}=useAuth();const query=useQueryClient();const [mobile,setMobile]=useState(false);const [collapsed,setCollapsed]=useState(false);const location=useLocation();
 if(loading)return <Loading/>;if(!user)return <Navigate to="/login"/>;if(user.must_change_password)return <Navigate to="/change-password"/>;
 const nav=[['/','Boshqaruv paneli',LayoutDashboard],...(user.role==='SUPER_ADMIN'?[['/teachers','O‘qituvchilar',Users] as const]:[]),['/quizzes',user.role==='SUPER_ADMIN'?'Testlar':'Testlarim',BookOpen],['/questions','Savollar',FileQuestion],['/students','O‘quvchilar',Users],['/profile','Profil',Settings]] as const;
 const links=<>{nav.map(([path,title,Icon])=><NavLink key={path as string} to={path as string} end={path==='/'} title={title as string} onClick={()=>setMobile(false)}><Icon size={20}/><span>{title as string}</span></NavLink>)}</>;
 return <div className={'shell '+(collapsed?'collapsed':'')}><a className="skip" href="#main">Asosiy tarkibga o‘tish</a><aside className="sidebar"><div className="brand"><span className="brand-icon"><GraduationCap/></span><span>Quiz Bot</span></div><div className="nav-label">BOSHQARUV</div><nav>{links}</nav><div className="sidebar-bottom"><div className="secure"><span className="dot"/> Himoyalangan muhit</div><button className="icon" aria-label="Menyuni yig‘ish" onClick={()=>setCollapsed(!collapsed)}><PanelLeftClose/></button></div></aside><div className="workspace"><header><button className="icon mobile-menu" aria-label="Menyuni ochish" onClick={()=>setMobile(true)}><Menu/></button><span className="breadcrumb">Quiz Bot <span>/</span> {nav.find(x=>x[0]===location.pathname)?.[1]||'Test tafsilotlari'}</span><div className="header-actions"><ThemeToggle/><NavLink className="avatar" to="/profile" aria-label="Profil">{(user.full_name||user.username).slice(0,1).toUpperCase()}</NavLink><div className="user-caption"><strong>{user.full_name||user.username}</strong><small>{user.role==='TEACHER'?'O‘qituvchi':'Administrator'}</small></div><button className="icon" aria-label="Hisobdan chiqish" onClick={async()=>{await post('auth/logout/');query.clear();refresh()}}><LogOut size={18}/></button></div></header><main id="main"><Outlet/></main><footer>Quiz Bot <span>Vaqt mintaqasi: Toshkent (UTC+5)</span></footer></div><Modal open={mobile} onOpenChange={setMobile} title="Navigatsiya"><nav className="mobile-nav">{links}</nav></Modal></div>
}
