import React, { useState } from 'react'
import useAxios from '../../utils/useAxios';
import { showToast } from '../../utils/toast';
import axios from 'axios';
import { useAuthStore } from '../../store/auth';
import DotsLoader from '../../components/DotsLoader';

const UploadAllegro: React.FC = () => {

  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const axios_ = useAxios();
  const user = useAuthStore((state) => state.allUserData);

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

    console.log("user_id", user.user_id);
    const myData = new FormData();
    myData.append("file", file);
    myData.append("user_id", user.user_id);
    setIsLoading(false);

    try {
      console.log('user...', user)
      const resp = await axios_.post("api/store/upload-csv", myData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setIsLoading(true);
      console.log("sendFile", resp);
      showToast("success", "Plik przesłany pomyślnie!");
    } catch (error) {
      showToast("error", "Coś poszło nie tak...");
    }
  };


  const deleteAllProducts = async () => {
    setIsLoading(false);
    try {
      const resp = await axios_.delete('api/store/delete-all-products')
      setIsLoading(true);
      showToast("success", "Wszystkie produkty zostały usunięte");
    } catch (error) {
      showToast("error", "Coś poszło nie tak...");
    }
  }

  const convertImages = async () => {
    setIsLoading(false);
    try {
      const resp = await axios_.post('api/store/convert-links-to-imgs')
      setIsLoading(true);
      showToast("success", "Wszystkie produkty zostały usunięte");
    } catch (error) {
      showToast("error", "Coś poszło nie tak...");
    }
  }


  return (
    <>
      {isLoading === true ? (
        <div className='flexColumnCenter gap-15'>
          <label htmlFor="file" className='fileUpload'>
            Importuj oferty
            <input id="file" type="file" onChange={handleFileChange} style={{ display: 'none' }} />
          </label>
          <button className='fileUpload' onClick={convertImages}>Zapisz zdjęcia</button>
          <button className='fileUpload' onClick={deleteAllProducts}>Usuń produkty</button>
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

export default UploadAllegro