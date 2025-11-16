import React, { useState } from 'react'
import useAxios from '../../utils/useAxios';
import { showToast } from '../../utils/toast';
import axios from 'axios';
import { useAuthStore } from '../../store/auth';
import DotsLoader from '../../components/DotsLoader';
import Cookies from 'js-cookie';
import { __userId } from '../../utils/auth';
import { responsiveFontSizes } from '@mui/material/styles';

const UploadKecja: React.FC = () => {

  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const axios_ = useAxios();
  const user = __userId(); 
  // console.log("user", user?.['user_id']);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      sendFile(e.target.files[0]);
    }
  };

  const sendFile = async (file: File) => {
    if (!file) {
      showToast("warning", "Wybierz plik");
      return;
    }

    const myData = new FormData();
    myData.append("file", file);
    myData.append("user_id", user?.['user_id']);
    setIsLoading(false);

    try {
      // const resp = await axios_.post("api/store/upload-csv", myData, {
      const resp = await axios_.post("api/store/upload-presta-csv", myData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setIsLoading(true);
      // console.log("sendFile", resp);
      showToast("success", "Plik przesłany pomyślnie!");
    } catch (error) {
      console.log("error - upload", error);
      // Axios errors often have response data here:
      if (error.response && error.response.data) {
        showToast("error", error.response.data.Błąd || "Coś poszło nie tak...");
      } else {
        showToast("error", "Coś poszło nie tak...");
      }
    }

  };

  return (
    <>
      {isLoading === true ? (
        <div className='flexColumnCenter gap-15'>
          <label htmlFor="file" className='fileUpload'>
            Importuj oferty - Kecja
            <input id="file" type="file" onChange={handleFileChange} style={{ display: 'none' }} />
          </label>
        </div>
      ) : (
        <div className='flexColumnCenter gap-15'>
          <DotsLoader />
          <p>Proszę czekać...</p>
        </div>
      )}
    </>
  )
}

export default UploadKecja