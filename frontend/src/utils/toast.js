import Swal from "sweetalert2";

const Toast = Swal.mixin({
    toast: true,
    position: "top",
    showConfirmButton: false,
    timer: 1500,
    timerProgressBar: true,
});

/**
 * Show a toast notification
 * @param {string} icon - "success", "error", "warning", "info", or "question"
 * @param {string} title - Message to display
 */
export const showToast = (icon, title) => {
    Toast.fire({
        icon,
        title,
    });
};
