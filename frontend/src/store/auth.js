import { create } from 'zustand';
import { mountStoreDevtool } from 'simple-zustand-devtools';


const useAuthStore = create((set, get) => ({
    allUserData: null,
    loading: false,

    user: () => ({
        user_id: get().allUserData?.user_id || null,
        username: get().allUserData?.username || null,
    }),

    setUser: (user) => set({ allUserData: user }),
    setLoading: (loading) => set({ loading }),
    isLoggedIn: () => get().allUserData !== null,

}))

if (import.meta.env.DEV) {
    mountStoreDevtool('Store', useAuthStore)
}

export { useAuthStore };


// // Import the 'create' function from the 'zustand' library.
// import { create } from 'zustand';

// // Import the 'mountStoreDevtool' function from the 'simple-zustand-devtools' library
// import { mountStoreDevtool } from 'simple-zustand-devtools';

// const useAuthStore = create<SessionState>(
//     persist(
//       (set) => ({
//         user: null,
//         accessToken: null,
//         refreshToken: null,
//         setUser: (user) => set({ user }),
//         setTokens: (accessToken, refreshToken) => set({ accessToken, refreshToken }),
//         logout: () => set({ user: null, accessToken: null, refreshToken: null }),
//       }),
//       {
//         name: "user-session", // the key used in localStorage to store the session
//         getStorage: () => localStorage, // use localStorage to persist the state
//       }
//     )
//   );

// // Export the 'useAuthStore' for use in other parts of the application.
// export { useAuthStore };
