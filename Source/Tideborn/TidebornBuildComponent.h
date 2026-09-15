#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "TidebornBuildComponent.generated.h"

class UTidebornInventoryComponent;
class AStaticMeshActor;

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
	float PlaceDistance = 400.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|Build")
	FName RequiredItemId = FName(TEXT("Foundation"));

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Tideborn|Build")
	bool bBuildMode = false;

	UFUNCTION(BlueprintCallable, Category="Tideborn|Build")
	void ToggleBuildMode();

	UFUNCTION(BlueprintCallable, Category="Tideborn|Build")
	bool TryCommitPlacement();

	TArray<FTransform> GetPlacedTransforms() const;
	void RestorePlaced(const TArray<FTransform>& Transforms);

private:
	UPROPERTY()
	TObjectPtr<AActor> GhostActor;

	UPROPERTY()
	TArray<TObjectPtr<AActor>> PlacedActors;

	FTransform GhostTransform;
	bool bGhostValid = false;

	void BindHotkeys();
	void OnToggleBuildKey();
	void UpdateGhost();
	AActor* SpawnBuildPiece(const FTransform& Xform, bool bGhost);
	UTidebornInventoryComponent* GetInventory() const;
};
