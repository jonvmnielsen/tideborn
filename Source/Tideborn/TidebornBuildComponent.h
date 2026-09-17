#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "TidebornBuildComponent.generated.h"

class UTidebornInventoryComponent;
class ATidebornBuildPiece;

UCLASS(ClassGroup=(Tideborn), meta=(BlueprintSpawnableComponent))
class TIDEBORN_API UTidebornBuildComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UTidebornBuildComponent();

	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|Build")
	float SnapSize = 100.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|Build")
	float PlaceDistance = 600.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|Build")
	FName RequiredItemId = FName(TEXT("Foundation"));

	UFUNCTION(BlueprintCallable, Category="Tideborn|Build")
	void BeginPlaceMode(FName PieceId);

	UFUNCTION(BlueprintCallable, Category="Tideborn|Build")
	void CancelPlaceMode();

	UFUNCTION(BlueprintCallable, Category="Tideborn|Build")
	bool IsPlaceMode() const { return bPlaceMode; }

	UFUNCTION(BlueprintCallable, Category="Tideborn|Build")
	bool TryCommitPlacement();

	TArray<FTransform> GetPlacedTransforms() const;
	void RestorePlaced(const TArray<FTransform>& Transforms);

private:
	UPROPERTY()
	TObjectPtr<ATidebornBuildPiece> GhostActor;

	UPROPERTY()
	TArray<TObjectPtr<ATidebornBuildPiece>> PlacedActors;

	FTransform GhostTransform;
	bool bPlaceMode = false;
	bool bGhostValid = false;

	void BindHotkeys();
	void OnPlaceClick();
	void OnCancelClick();
	void UpdateGhost();
	ATidebornBuildPiece* SpawnBuildPiece(const FTransform& Xform, bool bGhost);
	FVector SnapPlaceLocation(const FVector& Raw) const;
	UTidebornInventoryComponent* GetInventory() const;
};
